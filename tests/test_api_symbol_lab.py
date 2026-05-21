"""Slice 13.7 — FastAPI /api/symbol-lab contract tests."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP, SYMBOL_LAB_DEFAULT_TICKER
from api.main import create_app


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
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["header"]["ticker"] == SYMBOL_LAB_DEFAULT_TICKER
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


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
    assert body["recentBars"] == []
    assert body["position"] is None
    assert body["setupHint"] is not None


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
