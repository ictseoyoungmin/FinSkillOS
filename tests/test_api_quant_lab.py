"""Phase 21.2 — /api/quant-lab contract + SimulationService (live DB) tests.

Fixture-first endpoint that replays a declarative strategy spec over stored bars.
Descriptive-only: exposure ON/OFF, not-advice caption, no forbidden wording.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures.quant_lab import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.db.base import Base
from finskillos.guards.base import find_forbidden_term
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService
from finskillos.simulation.library import STRATEGY_LIBRARY, condition_text


def _client() -> TestClient:
    return TestClient(create_app())


def test_quant_lab_fixture_is_descriptive_and_renders() -> None:
    body = _client().get(
        "/api/quant-lab", headers={"X-FSO-Use-Fixture": "1"}
    ).json()

    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert body["strategy"]["id"] == "SMA_50_CROSS"
    assert len(body["equityCurve"]) > 0
    assert len(body["availableStrategies"]) == len(STRATEGY_LIBRARY)
    assert body["availableTickers"]
    assert "매매 권유" in body["safetyCaption"]
    # Every prose surface stays clear of forbidden execution wording.
    assert find_forbidden_term(body["safetyCaption"]) is None
    assert find_forbidden_term(body["judgment"]["summary"]) is None
    assert find_forbidden_term(body["strategy"]["description"]) is None


def test_quant_lab_unknown_strategy_falls_back_to_default_fixture() -> None:
    body = _client().get(
        "/api/quant-lab?strategy=NOPE", headers={"X-FSO-Use-Fixture": "1"}
    ).json()
    assert body["strategy"]["id"] == "SMA_50_CROSS"


def test_condition_text_renders_each_library_spec() -> None:
    for spec in STRATEGY_LIBRARY:
        entry = condition_text(spec.entry)
        exit_ = condition_text(spec.exit)
        assert entry and exit_
        assert "?" not in entry  # every condition variant is handled


def test_quant_lab_live_runs_strategy_over_stored_bars(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        market = MarketDataService(
            session,
            adapter=MockMarketDataAdapter(default_bars=90),
            universe=["NVDA"],
        )
        market.refresh_bars(["NVDA"])
        SignalService(session).compute_for_universe(["NVDA"])
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = _client().get("/api/quant-lab?strategy=SMA_50_CROSS&ticker=NVDA").json()

        assert body["systemStatus"]["db"] == "LIVE"
        assert body["dataState"]["source"] == "live"
        assert body["dataState"]["ticker"] == "NVDA"
        assert body["strategy"]["ticker"] == "NVDA"
        assert body["dataState"]["barCount"] > 0
        assert len(body["equityCurve"]) == body["dataState"]["barCount"]
        # Benchmark = buy-and-hold; both curves start near 1.0.
        assert abs(body["equityCurve"][0]["benchmark"] - 1.0) < 0.2
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert find_forbidden_term(body["safetyCaption"]) is None
        assert "NVDA" in body["availableTickers"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_quant_lab_live_missing_bars_is_explicit_live_state(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = _client().get("/api/quant-lab?strategy=SMA_50_CROSS&ticker=ZZZZ").json()
        # DB reachable but no bars → live-empty state, never the fixture sample.
        assert body["systemStatus"]["db"] == "LIVE"
        assert body["dataState"]["source"] == "live"
        assert body["equityCurve"] == []
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert find_forbidden_term(body["dataState"]["dataNote"]) is None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
