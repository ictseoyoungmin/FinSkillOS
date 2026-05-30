"""Slice 13.6 — FastAPI /api/control-room contract tests.

Verifies the shape the React shell relies on:

* All structural sections (ticker strip, mission, operating state,
  portfolio exposure, review queue, interpretation cards, risk
  firewall, catalyst watch, watchlist) are present.
* Field names are camelCase so the frontend can consume the JSON
  without re-mapping.
* The schema is interpretation-first: no execution-style fields
  (``buy`` / ``sell`` / ``execute`` / ``order``) are present
  anywhere in the response.
* The header opt-in `X-FSO-Use-Fixture` is accepted.
* The mocked `/api/mock/control-room` route always returns the
  deterministic fixture (used by Playwright visual baselines).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.fixtures import CONTROL_ROOM_FIXTURE_TIMESTAMP
from api.main import create_app
from api.routes.control_room import control_room
from finskillos.config import reset_settings_cache
from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.repositories import (
    AccountRepository,
    MarketRepository,
    SymbolSubscriptionRepository,
)
from finskillos.services.event_service import EventInput, EventLinkInput, EventService
from finskillos.services.portfolio_service import PortfolioPositionInput, PortfolioService

UTC = timezone.utc


def _client() -> TestClient:
    return TestClient(create_app())


def _fixture_json() -> dict:
    return _client().get(
        "/api/control-room",
        headers={"X-FSO-Use-Fixture": "1"},
    ).json()


def test_control_room_endpoint_returns_full_payload() -> None:
    response = _client().get(
        "/api/control-room",
        headers={"X-FSO-Use-Fixture": "1"},
    )
    assert response.status_code == 200
    body = response.json()

    # Top-level keys (camelCase).
    expected_top_level = {
        "generatedAt",
        "systemStatus",
        "dataState",
        "tickerStrip",
        "mission",
        "operatingState",
        "portfolioExposure",
        "reviewQueue",
        "interpretationCards",
        "riskFirewall",
        "catalystWatch",
        "watchlist",
        "marketTape",
        "source",
    }
    assert expected_top_level.issubset(body.keys())
    assert body["dataState"]["source"] == body["source"]
    assert body["dataState"]["overviewStatus"] == "OK"
    assert body["dataState"]["marketTapePoints"] == len(body["marketTape"])
    assert body["dataState"]["guardCount"] == len(body["riskFirewall"])
    assert body["dataState"]["catalystCount"] == len(body["catalystWatch"])
    assert body["dataState"]["watchlistCount"] == len(body["watchlist"])
    assert body["dataState"]["latestMarketAt"]
    assert body["dataState"]["latestEventAt"]
    assert body["dataState"]["latestWatchlistAt"]
    assert body["dataState"]["marketFreshnessStatus"] == "FRESH"
    assert body["dataState"]["catalystFreshnessStatus"] == "FRESH"
    assert body["dataState"]["watchlistFreshnessStatus"] == "FRESH"
    assert body["dataState"]["railFreshnessStatus"] == "FRESH"
    assert body["dataState"]["railFreshnessNote"]


def test_control_room_market_tape_is_normalised_and_nonempty() -> None:
    """13.6 cleanup §1 — Portfolio / Market Tape series must be wired."""

    body = _fixture_json()
    tape = body["marketTape"]
    assert isinstance(tape, list) and len(tape) >= 5, (
        "Control Room must surface a Portfolio / Market Tape series with "
        "at least 5 buckets so the chart panel always has data to render."
    )
    first = tape[0]
    portfolio_start = float(first["portfolio"])
    benchmark_start = float(first["benchmark"])
    # Series are normalised — both lines must start at the same value.
    assert portfolio_start == benchmark_start
    assert portfolio_start > 0
    for row in tape:
        assert {"label", "portfolio", "benchmark"}.issubset(row.keys())


def test_control_room_returns_deterministic_fixture_timestamp() -> None:
    body = _fixture_json()
    assert body["generatedAt"] == CONTROL_ROOM_FIXTURE_TIMESTAMP


def test_control_room_ticker_strip_has_expected_symbols() -> None:
    body = _fixture_json()
    symbols = {row["symbol"] for row in body["tickerStrip"]}
    # Slice-04 universe + macro proxies anchor the strip.
    must_have = {"SPY", "QQQ", "NVDA", "TSLA", "VIX"}
    assert must_have.issubset(symbols)


def test_control_room_mission_includes_progress_and_phase() -> None:
    body = _fixture_json()
    mission = body["mission"]
    assert "currentValue" in mission
    assert "targetValue" in mission
    assert "progressPct" in mission
    assert "phase" in mission
    assert float(mission["progressPct"]) > 0


def test_control_room_preparation_score_is_an_integer_in_range() -> None:
    body = _fixture_json()
    score = body["operatingState"]["preparationScore"]
    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_control_room_risk_firewall_lists_documented_guards() -> None:
    body = _fixture_json()
    guards = {row["name"] for row in body["riskFirewall"]}
    assert "SINGLE_POSITION_LIMIT_GUARD" in guards
    assert "DRAWDOWN_GUARD" in guards
    assert "SECTOR_CONCENTRATION_GUARD" in guards


def test_control_room_response_does_not_expose_execution_concepts() -> None:
    """Safety contract — interpretation-first JSON only."""

    raw = json.dumps(_fixture_json()).lower()
    for forbidden in (
        '"buy"',
        '"sell"',
        '"execute"',
        '"trade now"',
        '"order"',
        '"place_order"',
    ):
        assert forbidden not in raw, (
            f"Control Room response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted() -> None:
    response = _client().get(
        "/api/control-room", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_mock_control_room_route_returns_fixture() -> None:
    body = _client().get("/api/mock/control-room").json()
    assert body["source"] == "fixture"
    assert body["generatedAt"] == CONTROL_ROOM_FIXTURE_TIMESTAMP


def test_api_response_does_not_advertise_execution_endpoints() -> None:
    """OpenAPI document must not expose buy/sell/execute paths."""

    spec = _client().get("/openapi.json").json()
    paths = set(spec.get("paths", {}).keys())
    for forbidden in ("/api/buy", "/api/sell", "/api/order", "/api/execute"):
        assert forbidden not in paths, (
            f"OpenAPI exposes forbidden execution path {forbidden!r}"
        )


def test_control_room_live_empty_state_when_db_reachable(
    db_session: Session,
    monkeypatch,
) -> None:
    _patch_session_scope(monkeypatch, db_session)

    body = control_room(use_fixture=False).model_dump(by_alias=True)

    assert body["source"] == "live"
    assert body["dataState"]["source"] == "live"
    assert body["dataState"]["overviewStatus"] == "MISSING"
    assert body["dataState"]["missionStatus"] == "MISSING"
    assert body["dataState"]["latestMarketAt"] is None
    assert body["dataState"]["latestEventAt"] is None
    assert body["dataState"]["latestWatchlistAt"] is None
    assert body["dataState"]["marketFreshnessStatus"] == "MISSING"
    assert body["dataState"]["catalystFreshnessStatus"] == "MISSING"
    assert body["dataState"]["watchlistFreshnessStatus"] == "MISSING"
    assert body["dataState"]["railFreshnessStatus"] == "MISSING"
    assert body["dataState"]["railFreshnessNote"] == "No composed live rail rows yet."
    assert body["mission"]["progressPct"] == Decimal("0")
    assert body["riskFirewall"] == []
    assert body["reviewQueue"][0]["title"] == "Account baseline"


def test_control_room_promotes_live_mission_portfolio_and_guards(
    db_session: Session,
    monkeypatch,
) -> None:
    _seed_account_and_portfolio(db_session)
    _patch_session_scope(monkeypatch, db_session)

    body = control_room(use_fixture=False).model_dump(by_alias=True)

    assert body["source"] == "live"
    assert body["dataState"]["overviewStatus"] == "PARTIAL"
    assert body["dataState"]["missionStatus"] == "OK"
    assert body["dataState"]["guardStatus"] == "OK"
    assert body["mission"]["progressPct"] > 0
    assert body["portfolioExposure"]
    assert body["riskFirewall"]
    assert body["systemStatus"]["guardCount"] <= len(body["riskFirewall"])


def test_control_room_promotes_live_overview_rails(
    db_session: Session,
    monkeypatch,
) -> None:
    _seed_account_and_portfolio(db_session)
    ts = datetime(2026, 5, 28, 14, 0, tzinfo=UTC)
    _seed_market_series(db_session, "SPY", Decimal("670"), ts)
    _seed_market_series(db_session, "QQQ", Decimal("550"), ts)
    _seed_market_series(db_session, "NVDA", Decimal("170"), ts)
    SymbolSubscriptionRepository(db_session).subscribe("NVDA", name="NVIDIA")
    EventService(db_session).create_event(
        EventInput(
            title="NVIDIA earnings window",
            event_type="EARNINGS",
            date_status="TENTATIVE",
            start_date=date(2026, 6, 3),
            source="company_calendar",
            importance_score=Decimal("3.0"),
        ),
        links=(EventLinkInput(ticker="NVDA", sector="Semiconductors"),),
    )
    _patch_session_scope(monkeypatch, db_session)

    body = control_room(use_fixture=False).model_dump(by_alias=True)

    assert body["source"] == "live"
    assert body["dataState"]["marketTapeStatus"] == "OK"
    assert body["dataState"]["catalystStatus"] == "OK"
    assert body["dataState"]["watchlistStatus"] == "OK"
    assert body["dataState"]["marketTapePoints"] == len(body["marketTape"])
    assert body["dataState"]["latestMarketAt"].startswith("2026-05-30T14:00:00")
    assert body["dataState"]["latestEventAt"] == "2026-06-03"
    assert body["dataState"]["latestWatchlistAt"].startswith("2026-05-30T14:00:00")
    assert body["dataState"]["marketFreshnessStatus"] == "FRESH"
    assert body["dataState"]["catalystFreshnessStatus"] == "FRESH"
    assert body["dataState"]["watchlistFreshnessStatus"] == "FRESH"
    assert body["dataState"]["railFreshnessStatus"] == "FRESH"
    assert "market 2026-05-30" in body["dataState"]["railFreshnessNote"]
    assert body["tickerStrip"][0]["symbol"] == "NVDA"
    assert body["catalystWatch"][0]["title"] == "NVIDIA earnings window"
    assert body["watchlist"][0]["symbol"] == "NVDA"


def test_control_room_classifies_stale_market_and_watchlist_rails(
    db_session: Session,
    monkeypatch,
) -> None:
    _seed_account_and_portfolio(db_session)
    stale_ts = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    _seed_market_series(db_session, "SPY", Decimal("670"), stale_ts)
    _seed_market_series(db_session, "QQQ", Decimal("550"), stale_ts)
    _seed_market_series(db_session, "NVDA", Decimal("170"), stale_ts)
    SymbolSubscriptionRepository(db_session).subscribe("NVDA", name="NVIDIA")
    _patch_session_scope(monkeypatch, db_session)

    body = control_room(use_fixture=False).model_dump(by_alias=True)

    assert body["dataState"]["marketTapeStatus"] == "OK"
    assert body["dataState"]["watchlistStatus"] == "OK"
    assert body["dataState"]["marketFreshnessStatus"] == "STALE"
    assert body["dataState"]["catalystFreshnessStatus"] == "MISSING"
    assert body["dataState"]["watchlistFreshnessStatus"] == "STALE"
    assert body["dataState"]["railFreshnessStatus"] == "STALE"
    assert "market 2026-05-03" in body["dataState"]["railFreshnessNote"]
    assert body["dataState"]["marketStaleAfterDays"] == 3
    assert body["dataState"]["watchlistStaleAfterDays"] == 3


def test_control_room_freshness_threshold_is_configurable(
    db_session: Session,
    monkeypatch,
) -> None:
    _seed_account_and_portfolio(db_session)
    stale_ts = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    _seed_market_series(db_session, "SPY", Decimal("670"), stale_ts)
    _seed_market_series(db_session, "QQQ", Decimal("550"), stale_ts)
    _seed_market_series(db_session, "NVDA", Decimal("170"), stale_ts)
    SymbolSubscriptionRepository(db_session).subscribe("NVDA", name="NVIDIA")
    _patch_session_scope(monkeypatch, db_session)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS", "3650")
    monkeypatch.delenv("FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS", raising=False)
    monkeypatch.delenv(
        "FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS", raising=False
    )
    reset_settings_cache()

    try:
        body = control_room(use_fixture=False).model_dump(by_alias=True)

        # A wide threshold reclassifies the otherwise-stale market rail as FRESH.
        assert body["dataState"]["marketStaleAfterDays"] == 3650
        assert body["dataState"]["watchlistStaleAfterDays"] == 3650
        assert body["dataState"]["marketFreshnessStatus"] == "FRESH"
        assert "stale > 3650d" in body["dataState"]["railFreshnessNote"]
    finally:
        reset_settings_cache()


def test_control_room_freshness_threshold_supports_per_rail_override(
    db_session: Session,
    monkeypatch,
) -> None:
    _seed_account_and_portfolio(db_session)
    stale_ts = datetime(2026, 5, 1, 14, 0, tzinfo=UTC)
    _seed_market_series(db_session, "SPY", Decimal("670"), stale_ts)
    SymbolSubscriptionRepository(db_session).subscribe("NVDA", name="NVIDIA")
    _patch_session_scope(monkeypatch, db_session)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.delenv("FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS", raising=False)
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS", "3650")
    monkeypatch.setenv("FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS", "7")
    reset_settings_cache()

    try:
        body = control_room(use_fixture=False).model_dump(by_alias=True)

        assert body["dataState"]["marketStaleAfterDays"] == 3650
        assert body["dataState"]["watchlistStaleAfterDays"] == 7
        assert (
            "stale > 3650d market / 7d watchlist"
            in body["dataState"]["railFreshnessNote"]
        )
    finally:
        reset_settings_cache()


def _patch_session_scope(monkeypatch, db_session: Session) -> None:
    @contextmanager
    def _scope() -> Iterator[Session]:
        yield db_session

    monkeypatch.setattr("api.routes.control_room.get_session_scope", _scope)


def _seed_account_and_portfolio(session: Session) -> None:
    account = AccountRepository(session).create(
        name="Control Room API Account",
        target_value=Decimal("100000000"),
    )
    PortfolioService(session).import_snapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 28),
        rows=[
            PortfolioPositionInput(
                ticker="NVDA",
                quantity=Decimal("1"),
                market_value=Decimal("20000000"),
                sector="Semiconductors",
            ),
            PortfolioPositionInput(
                ticker="TSLA",
                quantity=Decimal("1"),
                market_value=Decimal("12000000"),
                sector="Consumer Discretionary",
            ),
        ],
        cash_value=Decimal("8000000"),
        peak_value=Decimal("45000000"),
        drawdown_pct=Decimal("-4.20"),
    )


def _seed_market_series(
    session: Session,
    ticker: str,
    close: Decimal,
    ts: datetime,
) -> None:
    repo = MarketRepository(session)
    for offset in range(3):
        value = close + Decimal(offset)
        repo.upsert_bar(
            MarketBarDTO(
                ticker=ticker,
                timeframe="1d",
                bar_time=ts + timedelta(days=offset),
                open=value,
                high=value,
                low=value,
                close=value,
                volume=Decimal("1000000"),
                source="test",
            )
        )
