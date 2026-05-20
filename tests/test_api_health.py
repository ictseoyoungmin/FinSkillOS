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
