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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.seed import seed_default_account


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


def test_risk_firewall_can_return_live_db_read_model(monkeypatch, tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'risk_firewall.db'}"
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    reset_settings_cache()

    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        seed_default_account(session)
        session.commit()

    try:
        response = TestClient(create_app()).get("/api/risk-firewall")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "live"
        assert body["systemStatus"]["db"] == "LIVE"
        assert body["systemStatus"]["mode"] == "READ_MODE"
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert len(body["guards"]) >= 6
    finally:
        reset_settings_cache()
        engine.dispose()


def test_risk_firewall_falls_back_to_fixture_when_live_db_has_no_account(
    monkeypatch,
    tmp_path,
) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'empty_risk_firewall.db'}"
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    reset_settings_cache()

    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)

    try:
        response = TestClient(create_app()).get("/api/risk-firewall")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "fixture"
        assert body["generatedAt"] == FIXTURE_TIMESTAMP
    finally:
        reset_settings_cache()
        engine.dispose()
