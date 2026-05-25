"""Slice 13.6 — FastAPI /api/health smoke."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app


def test_health_endpoint_returns_ok_status() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "finskillos-api"
    assert body["mode"] == "READ_MODE"
    assert "generatedAt" in body


def test_health_endpoint_emits_camelcase_field_names() -> None:
    """The React frontend expects camelCase JSON; snake_case would break it."""

    client = TestClient(create_app())
    body = client.get("/api/health").json()
    assert "generatedAt" in body
    assert "generated_at" not in body


def test_system_status_endpoint_returns_operations_contract() -> None:
    client = TestClient(create_app())
    response = client.get("/api/system-status")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "mode",
        "apiStatus",
        "dbStatus",
        "source",
        "dataCompleteness",
        "latestPortfolioSnapshotAt",
        "latestMarketBarAt",
        "latestIndicatorAt",
        "latestRegimeAt",
        "latestNewsAt",
        "latestEventAt",
        "staleFlags",
        "protocolAvailability",
    }
    assert expected.issubset(body.keys())
    assert body["mode"] == "READ_MODE"
    assert body["apiStatus"] == "LIVE"
    assert body["dbStatus"] in {"LIVE", "MISSING"}
    assert body["source"] in {"fixture", "live"}
    assert body["dataCompleteness"] in {"complete", "partial", "missing"}
    assert isinstance(body["staleFlags"], list)
    assert {item["key"] for item in body["protocolAvailability"]} == {
        "seed_sample_account",
        "refresh_market_data",
        "seed_sample_events",
        "recompute_regime",
        "run_risk_guards",
    }


def test_system_status_endpoint_emits_camelcase_field_names() -> None:
    client = TestClient(create_app())
    body = client.get("/api/system-status").json()

    assert "generatedAt" in body
    assert "dbStatus" in body
    assert "dataCompleteness" in body
    assert "latestMarketBarAt" in body
    assert "protocolAvailability" in body
    assert "generated_at" not in body
    assert "db_status" not in body
    assert "data_completeness" not in body
    assert "latest_market_bar_at" not in body
