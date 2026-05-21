"""Slice 13.8 — FastAPI /api/risk-firewall contract tests.

Verifies the shape the React Risk Firewall page relies on:

* All structural sections (guards, active alerts, protocol panel) are
  present.
* Field names are camelCase so the frontend can consume the JSON
  without re-mapping.
* The schema stays descriptive: no execution-style fields appear
  anywhere in the response.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_risk_firewall_returns_full_payload() -> None:
    response = _client().get("/api/risk-firewall")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "overallStatus",
        "overallRiskLevel",
        "guards",
        "activeAlerts",
        "protocol",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert body["overallStatus"] in {"PASS", "WARN", "FAIL", "BLOCKED", "INFO"}


def test_risk_firewall_guards_include_all_camelcase_fields() -> None:
    body = _client().get("/api/risk-firewall").json()
    assert len(body["guards"]) >= 6
    expected_fields = {"name", "status", "riskLevel", "title", "message"}
    for guard in body["guards"]:
        assert expected_fields.issubset(guard.keys()), guard


def test_risk_firewall_active_alerts_are_structured() -> None:
    body = _client().get("/api/risk-firewall").json()
    alerts = body["activeAlerts"]
    assert len(alerts) >= 1
    for alert in alerts:
        for key in ("alertDate", "severity", "guardName", "title", "message"):
            assert key in alert, alert
        assert alert["severity"] in {"INFO", "YELLOW", "ORANGE", "RED"}


def test_risk_firewall_protocol_panel_lists_three_tones() -> None:
    body = _client().get("/api/risk-firewall").json()
    tones = {entry["tone"] for entry in body["protocol"]}
    assert tones == {"allowed", "limited", "blocked"}


def test_risk_firewall_safety_caption_describes_read_mode() -> None:
    body = _client().get("/api/risk-firewall").json()
    caption = body["safetyCaption"].lower()
    assert "read mode" in caption
    assert "never modifies" in caption


def test_risk_firewall_response_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_client().get("/api/risk-firewall").json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"place_order"', '"order"'):
        assert forbidden not in raw, (
            f"Risk Firewall response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_risk_firewall() -> None:
    response = _client().get(
        "/api/risk-firewall", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"
