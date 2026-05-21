"""Slice 13.8 — FastAPI /api/mission-control contract tests."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_mission_control_returns_full_payload() -> None:
    response = _client().get("/api/mission-control")
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
    body = _client().get("/api/mission-control").json()
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
    body = _client().get("/api/mission-control").json()
    milestones = body["milestones"]
    pcts = [m["pct"] for m in milestones]
    assert pcts == [25, 50, 75, 100]
    for milestone in milestones:
        assert milestone["state"] in {"COMPLETED", "APPROACHING", "PENDING"}


def test_mission_control_portfolio_snapshot_fields_present() -> None:
    body = _client().get("/api/mission-control").json()
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
    body = _client().get("/api/mission-control").json()
    tones = {slice_["tone"] for slice_ in body["capitalMap"]}
    assert tones.issubset({"info", "warning", "danger", "neutral", "success"})


def test_mission_control_challenge_caption_mentions_challenge() -> None:
    body = _client().get("/api/mission-control").json()
    caption = body["challengeStatusCaption"].lower()
    assert "challenge" in caption


def test_mission_control_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/mission-control").json()).lower()
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
