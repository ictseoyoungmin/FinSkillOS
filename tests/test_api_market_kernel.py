"""Slice 13.7 — FastAPI /api/market-kernel contract tests.

Verifies the shape the React Market Kernel page relies on:

* All structural sections (universe, header, bars, indicators,
  events, watchpoints, interpretation) are present.
* Field names are camelCase so the frontend can consume the JSON
  without re-mapping.
* The schema is interpretation-first: no execution-style fields
  appear anywhere in the response.
* Unknown tickers degrade to a MISSING-status payload with a setup
  hint, never a 500.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import (
    FIXTURE_TIMESTAMP,
    MARKET_KERNEL_DEFAULT_TICKER,
    SUPPORTED_FOCUS_TICKERS,
)
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.base import Base
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService


def _client() -> TestClient:
    return TestClient(create_app())


def test_market_kernel_default_ticker_returns_full_payload() -> None:
    response = _client().get("/api/market-kernel")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "dataState",
        "universe",
        "header",
        "bars",
        "indicators",
        "events",
        "watchpoints",
        "interpretation",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["header"]["ticker"] == MARKET_KERNEL_DEFAULT_TICKER
    assert body["header"]["dataStatus"] == "OK"
    assert body["dataState"]["chartStatus"] == "OK"
    assert body["dataState"]["chartEvidence"] in {"fixture", "stored"}
    assert body["dataState"]["coverageLevel"] == "COMPLETE"
    assert body["dataState"]["evidenceCoveragePercent"] == 100
    assert body["dataState"]["barCount"] >= len(body["bars"])
    assert body["dataState"]["missingSummary"] == "No missing market-kernel evidence."
    if body["source"] == "fixture":
        assert body["generatedAt"] == FIXTURE_TIMESTAMP
    else:
        assert body["generatedAt"] != FIXTURE_TIMESTAMP


def test_market_kernel_universe_contains_focus_set() -> None:
    body = _client().get("/api/market-kernel").json()
    symbols = {row["symbol"] for row in body["universe"]}
    assert set(SUPPORTED_FOCUS_TICKERS).issubset(symbols)
    macro_kinds = {row["kind"] for row in body["universe"]}
    assert "MACRO_PROXY" in macro_kinds


def test_market_kernel_bars_are_chronological_and_have_close() -> None:
    body = _client().get("/api/market-kernel?ticker=NVDA").json()
    bars = body["bars"]
    assert len(bars) >= 15
    last_time = ""
    for bar in bars:
        assert {"barTime", "close"}.issubset(bar.keys())
        assert bar["barTime"] >= last_time, "bars must be ascending"
        last_time = bar["barTime"]


def test_market_kernel_indicators_block_has_required_fields() -> None:
    # Forced fixture so the indicator block / trendState are deterministic
    # regardless of whether a seeded DB promotes this route to live.
    body = _client().get(
        "/api/market-kernel?ticker=NVDA",
        headers={"X-FSO-Use-Fixture": "1"},
    ).json()
    indicators = body["indicators"]
    expected = {
        "rsi14",
        "ema20",
        "ema60",
        "ema120",
        "bbPosition",
        "volumeZScore",
        "momentumScore",
        "trendState",
    }
    assert expected.issubset(indicators.keys())
    assert indicators["trendState"] == "BULLISH"


def test_market_kernel_safety_caption_is_descriptive() -> None:
    body = _client().get("/api/market-kernel").json()
    caption = body["safetyCaption"].lower()
    assert "stored data only" in caption
    assert "not prediction" in caption


def test_market_kernel_ticker_query_is_uppercased() -> None:
    body = _client().get("/api/market-kernel?ticker=tsla").json()
    assert body["header"]["ticker"] == "TSLA"
    assert body["header"]["dataStatus"] == "OK"


def test_market_kernel_unknown_ticker_returns_missing_status() -> None:
    body = _client().get("/api/market-kernel?ticker=ZZZZZ").json()
    assert body["header"]["dataStatus"] == "MISSING"
    assert body["bars"] == []
    assert body["setupHint"] is not None
    assert body["dataState"]["chartStatus"] == "MISSING"


def test_market_kernel_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/market-kernel").json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"place_order"'):
        assert forbidden not in raw, (
            f"Market Kernel response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_market_kernel() -> None:
    response = _client().get(
        "/api/market-kernel", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_market_kernel_can_return_live_db_bars(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        market_service = MarketDataService(
            session,
            adapter=MockMarketDataAdapter(default_bars=30),
            universe=["SPY"],
        )
        market_service.refresh_bars(["SPY"])
        SignalService(session).compute_for_universe(["SPY"])
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/market-kernel?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["systemStatus"]["db"] == "LIVE"
        assert body["header"]["ticker"] == "SPY"
        assert body["header"]["dataStatus"] == "OK"
        assert body["dataState"]["chartEvidence"] == "stored"
        assert body["dataState"]["coverageLevel"] in {"COMPLETE", "PARTIAL"}
        assert body["dataState"]["evidenceCoveragePercent"] >= 85
        assert body["dataState"]["barCount"] == 30
        assert body["dataState"]["indicatorStatus"] in {"AVAILABLE", "PARTIAL"}
        assert len(body["bars"]) == 30
        assert body["indicators"]["rsi14"] is not None
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_market_kernel_event_overlay_includes_relevant_events(
    monkeypatch, tmp_path
) -> None:
    from datetime import date

    from finskillos.db.models.event import (
        DATE_STATUS_TENTATIVE,
        DATE_STATUS_WINDOW,
        EVENT_TYPE_CENTRAL_BANK,
        EVENT_TYPE_EARNINGS,
    )
    from finskillos.services.event_service import (
        EventInput,
        EventLinkInput,
        EventService,
    )

    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    today = date.today()
    with factory() as session:
        MarketDataService(
            session,
            adapter=MockMarketDataAdapter(default_bars=30),
            universe=["NVDA"],
        ).refresh_bars(["NVDA"])
        SignalService(session).compute_for_universe(["NVDA"])
        events = EventService(session)
        events.create_event(
            EventInput(
                title="NVDA earnings window",
                event_type=EVENT_TYPE_EARNINGS,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=today + timedelta(days=5),
            ),
            links=(EventLinkInput(ticker="NVDA", theme="AI"),),
        )
        events.create_event(
            EventInput(
                title="FOMC decision window",
                event_type=EVENT_TYPE_CENTRAL_BANK,
                date_status=DATE_STATUS_WINDOW,
                start_date=today + timedelta(days=10),
            ),
            links=(EventLinkInput(event_key="FOMC"),),
        )
        events.create_event(
            EventInput(
                title="TSLA delivery window",
                event_type=EVENT_TYPE_EARNINGS,
                date_status=DATE_STATUS_TENTATIVE,
                start_date=today + timedelta(days=7),
            ),
            links=(EventLinkInput(ticker="TSLA"),),
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/market-kernel?ticker=NVDA").json()

        assert body["source"] == "live"
        assert body["dataState"]["eventOverlayStatus"] == "AVAILABLE"
        titles = {event["title"] for event in body["events"]}
        assert "NVDA earnings window" in titles  # ticker-linked
        assert "FOMC decision window" in titles  # market-wide macro
        assert "TSLA delivery window" not in titles  # unrelated ticker excluded
        item = next(e for e in body["events"] if e["title"] == "NVDA earnings window")
        assert {"daysToEvent", "title", "subtitle", "tag", "tone"}.issubset(item)
        assert item["tag"] == "Tentative"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_market_kernel_live_db_missing_ticker_is_explicit(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/market-kernel?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["header"]["dataStatus"] == "MISSING"
        assert body["dataState"]["chartStatus"] == "MISSING"
        assert body["dataState"]["chartEvidence"] == "missing"
        assert body["dataState"]["coverageLevel"] == "EMPTY"
        assert body["dataState"]["evidenceCoveragePercent"] == 0
        assert body["dataState"]["missingSummary"] == "SPY needs stored bars and indicators."
        assert body["bars"] == []
        assert "no stored bar series" in body["interpretation"].lower()
        assert body["setupHint"] is not None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_market_kernel_ignores_future_stored_bars(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime.now(tz=timezone.utc)
    with factory() as session:
        MarketDataService(session).import_bars(
            [
                MarketBarDTO(
                    ticker="SPY",
                    timeframe="1d",
                    bar_time=now - timedelta(days=1),
                    open=Decimal("100"),
                    high=Decimal("101"),
                    low=Decimal("99"),
                    close=Decimal("100"),
                    volume=Decimal("1000000"),
                    source="test",
                ),
                MarketBarDTO(
                    ticker="SPY",
                    timeframe="1d",
                    bar_time=now + timedelta(days=1),
                    open=Decimal("200"),
                    high=Decimal("201"),
                    low=Decimal("199"),
                    close=Decimal("200"),
                    volume=Decimal("1000000"),
                    source="test",
                ),
            ]
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/market-kernel?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["header"]["latestClose"] == "100.000000"
        assert body["dataState"]["barCount"] == 1
        assert body["dataState"]["coverageLevel"] == "SPARSE"
        assert body["dataState"]["evidenceCoveragePercent"] == 4
        assert body["dataState"]["missingSummary"] == (
            "SPY has 1 of 20 stored bars; 19 more complete the indicator window."
        )
        assert len(body["bars"]) == 1
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_market_kernel_reads_requested_timeframe(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime.now(tz=timezone.utc)
    with factory() as session:
        MarketDataService(session).import_bars(
            [
                MarketBarDTO(
                    ticker="SPY",
                    timeframe="1wk",
                    bar_time=now - timedelta(weeks=offset),
                    open=Decimal("100"),
                    high=Decimal("101"),
                    low=Decimal("99"),
                    close=Decimal("100"),
                    volume=Decimal("1000000"),
                    source="test",
                )
                for offset in range(1, 6)
            ]
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        # Requested 1wk timeframe reads the stored weekly bars.
        weekly = _client().get("/api/market-kernel?ticker=SPY&timeframe=1wk").json()
        assert weekly["source"] == "live"
        assert weekly["header"]["timeframe"] == "1wk"
        assert len(weekly["bars"]) == 5
        assert weekly["dataState"]["chartStatus"] != "MISSING"

        # 1d has no stored bars -> explicit MISSING (DB-read-only, no provider).
        daily = _client().get("/api/market-kernel?ticker=SPY&timeframe=1d").json()
        assert daily["header"]["timeframe"] == "1d"
        assert daily["dataState"]["chartStatus"] == "MISSING"

        # Unsupported timeframe normalises to the 1d default.
        bad = _client().get("/api/market-kernel?ticker=SPY&timeframe=bogus").json()
        assert bad["header"]["timeframe"] == "1d"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
