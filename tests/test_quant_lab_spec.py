"""Phase 21.8 — free-form strategy spec JSON parsing/validation + /run endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures.quant_lab import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.data_sources import MockMarketDataAdapter
from finskillos.db.base import Base
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService
from finskillos.simulation.conditions import All, Compare, Cross
from finskillos.simulation.spec_json import (
    SpecParseError,
    condition_from_json,
    strategy_spec_from_json,
)


def test_condition_from_json_builds_each_kind() -> None:
    assert condition_from_json({"compare": ["rsi_14", "<", 30]}) == Compare(
        "rsi_14", "<", 30
    )
    assert condition_from_json({"cross": ["close", "above", "sma_20"]}) == Cross(
        "close", "above", "sma_20"
    )
    nested = condition_from_json(
        {"all": [{"compare": ["regime", "==", "RECOVERY"]},
                 {"compare": ["rsi_14", "<", 35]}]}
    )
    assert isinstance(nested, All) and len(nested.terms) == 2


@pytest.mark.parametrize(
    "bad",
    [
        {"compare": ["unknown_feat", "<", 1]},   # unknown feature
        {"compare": ["rsi_14", "≈", 1]},          # bad operator
        {"compare": ["close", ">", "abc"]},       # non-numeric for >
        {"cross": ["close", "sideways", "sma_20"]},  # bad direction
        {"two": 1, "keys": 2},                     # not single-key
        "nope",                                     # not an object
    ],
)
def test_condition_from_json_rejects_bad(bad) -> None:
    with pytest.raises(SpecParseError):
        condition_from_json(bad)


def test_strategy_spec_from_json_requires_fields() -> None:
    with pytest.raises(SpecParseError):
        strategy_spec_from_json({"entry": {}, "exit": {}})  # no ticker
    with pytest.raises(SpecParseError):
        strategy_spec_from_json({"ticker": "NVDA", "entry": {"compare": ["close", ">", 0]}})
    spec = strategy_spec_from_json(
        {
            "name": "내 전략",
            "ticker": "nvda",
            "entry": {"cross": ["close", "above", "sma_20"]},
            "exit": {"cross": ["close", "below", "sma_20"]},
        }
    )
    assert spec.strategy_id == "CUSTOM"
    assert spec.universe == ("NVDA",)
    assert spec.name == "내 전략"


def _seeded_db(tmp_path, ticker="NVDA", bars=90):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'q.db'}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as s:
        MarketDataService(
            s, adapter=MockMarketDataAdapter(default_bars=bars), universe=[ticker]
        ).refresh_bars([ticker])
        SignalService(s).compute_for_universe([ticker])
        s.commit()
    return database_url, engine


def test_quant_lab_run_endpoint_backtests_custom_spec(monkeypatch, tmp_path) -> None:
    database_url, engine = _seeded_db(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).post(
            "/api/quant-lab/run",
            json={
                "ticker": "NVDA",
                "name": "SMA20 돌파",
                "entry": {"cross": ["close", "above", "sma_20"]},
                "exit": {"cross": ["close", "below", "sma_20"]},
            },
        ).json()
        assert body["dataState"]["source"] == "live"
        assert body["strategy"]["id"] == "CUSTOM"
        assert body["strategy"]["name"] == "SMA20 돌파"
        assert body["strategy"]["ticker"] == "NVDA"
        assert body["strategy"]["entryText"]  # condition rendered
        assert len(body["equityCurve"]) == body["dataState"]["barCount"] > 0
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_quant_lab_screen_ranks_multiple_tickers(monkeypatch, tmp_path) -> None:
    # Seed two tickers, then screen one built-in strategy across both.
    database_url = f"sqlite+pysqlite:///{tmp_path / 'q.db'}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as s:
        MarketDataService(
            s, adapter=MockMarketDataAdapter(default_bars=90),
            universe=["NVDA", "AAPL"],
        ).refresh_bars(["NVDA", "AAPL"])
        SignalService(s).compute_for_universe(["NVDA", "AAPL"])
        s.commit()
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).get(
            "/api/quant-lab/screen?strategy=SMA_50_CROSS"
        ).json()
        tickers = {r["ticker"] for r in body["rows"]}
        assert {"NVDA", "AAPL"} <= tickers
        returns = [
            r["totalReturn"] for r in body["rows"] if r["totalReturn"] is not None
        ]
        assert returns == sorted(returns, reverse=True)  # ranked desc
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_quant_lab_portfolio_synthesizes_combined_curve(monkeypatch, tmp_path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'q.db'}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as s:
        MarketDataService(
            s, adapter=MockMarketDataAdapter(default_bars=90),
            universe=["NVDA", "AAPL"],
        ).refresh_bars(["NVDA", "AAPL"])
        SignalService(s).compute_for_universe(["NVDA", "AAPL"])
        s.commit()
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).get(
            "/api/quant-lab/portfolio?strategy=SMA_50_CROSS&tickers=NVDA,AAPL"
        ).json()
        assert sorted(body["tickers"]) == ["AAPL", "NVDA"]
        assert body["weight"] == 0.5
        assert len(body["curve"]) > 0
        assert body["curve"][0]["strategy"] > 0  # combined capital curve
        assert 0.0 <= body["curve"][-1]["exposure"] <= 1.0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_quant_lab_saved_specs_roundtrip(monkeypatch, tmp_path) -> None:
    database_url, engine = _seeded_db(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    client = TestClient(create_app())
    spec_body = {
        "name": "내 SMA20",
        "ticker": "NVDA",
        "entry": {"cross": ["close", "above", "sma_20"]},
        "exit": {"cross": ["close", "below", "sma_20"]},
    }
    try:
        # Save → returns an id; list shows it.
        saved = client.post("/api/quant-lab/specs", json=spec_body).json()
        spec_id = saved["id"]
        assert spec_id and saved["name"] == "내 SMA20"
        listing = client.get("/api/quant-lab/specs").json()
        assert any(s["id"] == spec_id for s in listing["specs"])
        # Run the saved spec by id.
        run = client.get(f"/api/quant-lab?saved={spec_id}").json()
        assert run["strategy"]["name"] == "내 SMA20"
        assert run["dataState"]["source"] == "live"
        assert len(run["equityCurve"]) > 0
        # Delete → gone from the list.
        assert client.delete(f"/api/quant-lab/specs/{spec_id}").json()["ok"] is True
        assert all(
            s["id"] != spec_id
            for s in client.get("/api/quant-lab/specs").json()["specs"]
        )
        # A bad spec is rejected on save (400).
        bad = client.post(
            "/api/quant-lab/specs",
            json={"ticker": "NVDA", "entry": {"compare": ["nope", "<", 1]},
                  "exit": {"compare": ["close", ">", 0]}},
        )
        assert bad.status_code == 400
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_quant_lab_run_rejects_bad_spec(monkeypatch, tmp_path) -> None:
    database_url, engine = _seeded_db(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = TestClient(create_app()).post(
            "/api/quant-lab/run",
            json={
                "ticker": "NVDA",
                "entry": {"compare": ["bogus", "<", 1]},
                "exit": {"compare": ["close", ">", 0]},
            },
        ).json()
        # Malformed spec → explicit state, never a crash.
        assert body["equityCurve"] == []
        assert "전략 정의 오류" in body["dataState"]["dataNote"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
