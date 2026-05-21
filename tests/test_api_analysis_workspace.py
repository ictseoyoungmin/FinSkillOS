"""Slice 13.7 — FastAPI /api/analysis-workspace contract tests."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_analysis_workspace_returns_full_payload() -> None:
    response = _client().get("/api/analysis-workspace")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "timeframe",
        "universe",
        "strongest",
        "weakest",
        "missingData",
        "regime",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["timeframe"] == "1d"
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_analysis_workspace_universe_covers_etfs_and_macro_proxies() -> None:
    body = _client().get("/api/analysis-workspace").json()
    universe = body["universe"]
    assert len(universe) >= 14
    kinds = {row["kind"] for row in universe}
    assert {"INDEX_ETF", "SECTOR_ETF", "MACRO_PROXY"}.issubset(kinds)
    tickers = {row["ticker"] for row in universe}
    assert {"SPY", "QQQ", "SMH", "VIX"}.issubset(tickers)


def test_analysis_workspace_strongest_weakest_are_ranked() -> None:
    body = _client().get("/api/analysis-workspace").json()
    strongest = body["strongest"]
    weakest = body["weakest"]
    assert len(strongest) == 3
    assert len(weakest) == 3

    strongest_scores = [float(row["relativeStrengthScore"]) for row in strongest]
    weakest_scores = [float(row["relativeStrengthScore"]) for row in weakest]
    assert strongest_scores == sorted(strongest_scores, reverse=True)
    assert weakest_scores == sorted(weakest_scores)
    assert strongest_scores[0] >= weakest_scores[-1]


def test_analysis_workspace_macro_proxies_are_excluded_from_ranking() -> None:
    body = _client().get("/api/analysis-workspace").json()
    ranked_tickers = {row["ticker"] for row in body["strongest"]} | {
        row["ticker"] for row in body["weakest"]
    }
    assert "VIX" not in ranked_tickers
    assert "DXY" not in ranked_tickers
    assert "US10Y" not in ranked_tickers


def test_analysis_workspace_regime_block_is_descriptive() -> None:
    regime = _client().get("/api/analysis-workspace").json()["regime"]
    assert regime is not None
    assert regime["regime"] == "RISK_ON_OVERHEAT"
    assert "not a price prediction" in regime["summary"].lower()


def test_analysis_workspace_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/analysis-workspace").json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"trade now"', '"order"'):
        assert forbidden not in raw, (
            f"Analysis Workspace response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_analysis_workspace() -> None:
    response = _client().get(
        "/api/analysis-workspace", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"
