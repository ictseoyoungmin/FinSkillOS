"""Slice 13.7 — FastAPI /api/symbol-lab contract tests."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP, SYMBOL_LAB_DEFAULT_TICKER
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository, AlertRepository, PositionRepository
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService


def _client() -> TestClient:
    return TestClient(create_app())


def test_symbol_lab_default_ticker_returns_full_payload() -> None:
    response = _client().get("/api/symbol-lab")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "header",
        "technical",
        "recentBars",
        "position",
        "alerts",
        "news",
        "regime",
        "watchpoints",
        "interpretation",
        "symbolUniverse",
        "identity",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["header"]["ticker"] == SYMBOL_LAB_DEFAULT_TICKER
    assert body["identity"]["ticker"] == SYMBOL_LAB_DEFAULT_TICKER
    assert body["identity"]["logoSource"] == "local_fallback"
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_symbol_lab_universe_exposes_all_searchable_symbols() -> None:
    body = _client().get("/api/symbol-lab").json()
    symbols = {row["symbol"] for row in body["symbolUniverse"]}
    assert symbols == {"NVDA", "TSLA", "AAPL", "MSFT", "SMH"}


def test_symbol_lab_default_ticker_has_position_context() -> None:
    body = _client().get("/api/symbol-lab").json()
    position = body["position"]
    assert position is not None
    assert position["ticker"] == "TSLA"
    assert position["sector"] == "Consumer Discretionary"
    assert position["overSinglePositionLimit"] is True


def test_symbol_lab_alerts_match_position_context() -> None:
    body = _client().get("/api/symbol-lab?ticker=TSLA").json()
    alerts = body["alerts"]
    assert any(
        alert["guardName"] == "SINGLE_POSITION_LIMIT_GUARD" for alert in alerts
    )


def test_symbol_lab_non_held_ticker_returns_none_position() -> None:
    body = _client().get("/api/symbol-lab?ticker=NVDA").json()
    assert body["header"]["ticker"] == "NVDA"
    assert body["position"] is None
    # NVDA still has technical data + watchpoints because we ship a
    # focus-ticker fixture for it.
    assert body["header"]["dataStatus"] == "OK"
    assert len(body["recentBars"]) > 0


def test_symbol_lab_unknown_ticker_returns_missing_status() -> None:
    body = _client().get("/api/symbol-lab?ticker=ZZZZZ").json()
    assert body["header"]["dataStatus"] == "MISSING"
    assert body["identity"]["avatarText"] == "ZZ"
    assert body["recentBars"] == []
    assert body["position"] is None
    assert body["symbolUniverse"]
    assert body["setupHint"] is not None


def test_symbol_lab_arbitrary_ticker_search_is_structured() -> None:
    body = _client().get("/api/symbol-lab?ticker=ADBE").json()
    assert body["header"]["ticker"] == "ADBE"
    assert body["header"]["dataStatus"] == "MISSING"
    assert "searched successfully" in body["setupHint"]


def test_symbol_lab_macro_proxy_is_input_search_only_until_snapshot_exists() -> None:
    body = _client().get("/api/symbol-lab?ticker=US10Y").json()
    shortcuts = {row["symbol"] for row in body["symbolUniverse"]}
    assert "US10Y" not in shortcuts
    assert body["header"]["ticker"] == "US10Y"
    assert body["header"]["dataStatus"] == "MISSING"


def test_symbol_lab_technical_block_has_required_fields() -> None:
    body = _client().get("/api/symbol-lab?ticker=NVDA").json()
    tech = body["technical"]
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
    assert expected.issubset(tech.keys())
    assert tech["trendState"] == "BULLISH"


def test_symbol_lab_safety_caption_is_descriptive() -> None:
    body = _client().get("/api/symbol-lab").json()
    caption = body["safetyCaption"].lower()
    assert "stored data only" in caption


def test_symbol_lab_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/symbol-lab").json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"trade now"', '"order"'):
        assert forbidden not in raw, (
            f"Symbol Lab response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_symbol_lab() -> None:
    response = _client().get(
        "/api/symbol-lab", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_symbol_lab_can_return_live_db_symbol_bars(monkeypatch, tmp_path) -> None:
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
        body = _client().get("/api/symbol-lab?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["systemStatus"]["db"] == "LIVE"
        assert body["header"]["ticker"] == "SPY"
        assert body["header"]["dataStatus"] == "OK"
        assert len(body["recentBars"]) == 30
        assert body["technical"]["rsi14"] is not None
        assert body["identity"]["ticker"] == "SPY"
        assert body["identity"]["logoSource"] == "local_fallback"
        assert body["position"] is None
        assert body["news"] == []
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_symbol_lab_live_db_missing_ticker_is_explicit(
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
        body = _client().get("/api/symbol-lab?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["header"]["dataStatus"] == "MISSING"
        assert body["recentBars"] == []
        assert "no stored bar series" in body["interpretation"].lower()
        assert body["setupHint"] is not None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_symbol_lab_live_db_attaches_position_context(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Test Account",
            target_value=Decimal("100000000"),
        )
        PositionRepository(session).create(
            account_id=account.id,
            ticker="SPY",
            quantity=Decimal("10"),
            market_value=Decimal("12000000"),
            sector="Index",
            theme="US large-cap",
            strategy_type="core",
            pnl_pct=Decimal("3.2"),
            thesis="Broad-market exposure review context.",
        )
        AlertRepository(session).create(
            account_id=account.id,
            alert_date=datetime.now(tz=timezone.utc).date(),
            guard_name="SINGLE_POSITION_LIMIT_GUARD",
            severity="YELLOW",
            title="SPY position review",
            message="SPY is above the configured review threshold.",
            payload={"ticker": "SPY"},
        )
        MarketDataService(
            session,
            adapter=MockMarketDataAdapter(default_bars=30),
            universe=["SPY"],
        ).refresh_bars(["SPY"])
        SignalService(session).compute_for_universe(["SPY"])
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/symbol-lab?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["position"]["ticker"] == "SPY"
        assert body["position"]["overSinglePositionLimit"] is True
        assert body["alerts"][0]["guardName"] == "SINGLE_POSITION_LIMIT_GUARD"
        assert body["systemStatus"]["guardCount"] == 1
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_symbol_lab_ignores_future_stored_bars(monkeypatch, tmp_path) -> None:
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
        body = _client().get("/api/symbol-lab?ticker=SPY").json()

        assert body["source"] == "live"
        assert body["header"]["latestClose"] == "100.000000"
        assert len(body["recentBars"]) == 1
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
