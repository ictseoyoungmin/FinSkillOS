"""Slice 13.8 — FastAPI /api/mission-control contract tests."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository
from finskillos.services.portfolio_service import (
    PortfolioPositionInput,
    PortfolioService,
)


def _client() -> TestClient:
    return TestClient(create_app())


def _fixture_get(client: TestClient):
    return client.get("/api/mission-control", headers={"X-FSO-Use-Fixture": "1"})


def test_mission_control_returns_full_payload() -> None:
    response = _fixture_get(_client())
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "goal",
        "milestones",
        "portfolio",
        "capitalMap",
        "themeMap",
        "challengeStatusCaption",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_mission_control_goal_has_camelcase_fields() -> None:
    body = _fixture_get(_client()).json()
    goal = body["goal"]
    expected = {
        "currentValue",
        "targetValue",
        "remainingValue",
        "progressPct",
        "progressRatio",
        "goalMode",
        "earlyStopTriggered",
        "phase",
        "challengeLabel",
    }
    assert expected.issubset(goal.keys())
    # Strings (Decimal -> string) for arithmetic safety on the React side.
    assert float(goal["progressPct"]) == 73.4


def test_mission_control_milestones_cover_quarter_steps() -> None:
    body = _fixture_get(_client()).json()
    milestones = body["milestones"]
    pcts = [m["pct"] for m in milestones]
    assert pcts == [25, 50, 75, 100]
    for milestone in milestones:
        assert milestone["state"] in {"COMPLETED", "APPROACHING", "PENDING"}


def test_mission_control_portfolio_snapshot_fields_present() -> None:
    body = _fixture_get(_client()).json()
    snapshot = body["portfolio"]
    expected = {
        "totalValue",
        "cashValue",
        "positionCount",
        "largestPositionTicker",
        "largestPositionWeightPct",
        "overSingleLimitTickers",
    }
    assert expected.issubset(snapshot.keys())
    assert snapshot["positionCount"] >= 1


def test_mission_control_capital_map_has_descriptive_tones() -> None:
    body = _fixture_get(_client()).json()
    tones = {slice_["tone"] for slice_ in body["capitalMap"]}
    assert tones.issubset({"info", "warning", "danger", "neutral", "success"})


def test_mission_control_challenge_caption_mentions_challenge() -> None:
    body = _fixture_get(_client()).json()
    caption = body["challengeStatusCaption"].lower()
    assert "challenge" in caption


def test_mission_control_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_fixture_get(_client()).json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"order"', '"place_order"'):
        assert forbidden not in raw, (
            f"Mission Control response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_mission_control() -> None:
    response = _client().get(
        "/api/mission-control", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_mission_control_reads_live_db_snapshot(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "mission.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account",
            target_value=Decimal("100000000"),
        )
        PortfolioService(session).import_snapshot(
            account_id=account.id,
            snapshot_date=date(2026, 5, 27),
            cash_value=Decimal("5000000"),
            rows=[
                PortfolioPositionInput(
                    ticker="NVDA",
                    quantity=Decimal("10"),
                    market_value=Decimal("25000000"),
                    sector="Semiconductors",
                    theme="AI Infrastructure",
                ),
                PortfolioPositionInput(
                    ticker="AAPL",
                    quantity=Decimal("8"),
                    market_value=Decimal("10000000"),
                    sector="Technology",
                    theme="Mega Cap Tech",
                ),
            ],
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().get("/api/mission-control")
        body = response.json()

        assert response.status_code == 200
        assert body["source"] == "live"
        assert body["goal"]["currentValue"] == "40000000.00"
        assert body["goal"]["progressPct"] == "40.00"
        assert body["portfolio"]["positionCount"] == 2
        assert body["portfolio"]["largestPositionTicker"] == "NVDA"
        assert body["capitalMap"][0]["label"] == "Semiconductors"
        assert body["themeMap"][0]["label"] == "AI Infrastructure"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
