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

from fastapi.testclient import TestClient

from api.fixtures import CONTROL_ROOM_FIXTURE_TIMESTAMP
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_control_room_endpoint_returns_full_payload() -> None:
    response = _client().get("/api/control-room")
    assert response.status_code == 200
    body = response.json()

    # Top-level keys (camelCase).
    expected_top_level = {
        "generatedAt",
        "systemStatus",
        "tickerStrip",
        "mission",
        "operatingState",
        "portfolioExposure",
        "reviewQueue",
        "interpretationCards",
        "riskFirewall",
        "catalystWatch",
        "watchlist",
        "source",
    }
    assert expected_top_level.issubset(body.keys())


def test_control_room_returns_deterministic_fixture_timestamp() -> None:
    body = _client().get("/api/control-room").json()
    assert body["generatedAt"] == CONTROL_ROOM_FIXTURE_TIMESTAMP


def test_control_room_ticker_strip_has_expected_symbols() -> None:
    body = _client().get("/api/control-room").json()
    symbols = {row["symbol"] for row in body["tickerStrip"]}
    # Slice-04 universe + macro proxies anchor the strip.
    must_have = {"SPY", "QQQ", "NVDA", "TSLA", "VIX"}
    assert must_have.issubset(symbols)


def test_control_room_mission_includes_progress_and_phase() -> None:
    body = _client().get("/api/control-room").json()
    mission = body["mission"]
    assert "currentValue" in mission
    assert "targetValue" in mission
    assert "progressPct" in mission
    assert "phase" in mission
    assert float(mission["progressPct"]) > 0


def test_control_room_preparation_score_is_an_integer_in_range() -> None:
    body = _client().get("/api/control-room").json()
    score = body["operatingState"]["preparationScore"]
    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_control_room_risk_firewall_lists_documented_guards() -> None:
    body = _client().get("/api/control-room").json()
    guards = {row["name"] for row in body["riskFirewall"]}
    assert "SINGLE_POSITION_LIMIT_GUARD" in guards
    assert "DRAWDOWN_GUARD" in guards
    assert "SECTOR_CONCENTRATION_GUARD" in guards


def test_control_room_response_does_not_expose_execution_concepts() -> None:
    """Safety contract — interpretation-first JSON only."""

    raw = json.dumps(_client().get("/api/control-room").json()).lower()
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
