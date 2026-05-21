"""Slice 13.8 — FastAPI /api/system-ops contract tests.

Covers:

* The GET protocol catalogue (camelCase shape, safe wording).
* Every POST /api/system-ops/<protocol> endpoint returns a
  structured ``ProtocolRunResult`` even in fixture-first mode (no
  DB session available) — the API contract forbids HTML / raw stack
  trace responses.
* Forbidden execution captions never appear in protocol metadata.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app

_PROTOCOL_KEYS = {
    "seed_sample_account",
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
}

_POST_ENDPOINTS = (
    ("/api/system-ops/seed-sample-account", "seed_sample_account"),
    ("/api/system-ops/recompute-regime", "recompute_regime"),
    ("/api/system-ops/run-risk-guards", "run_risk_guards"),
    ("/api/system-ops/seed-sample-events", "seed_sample_events"),
)

_FORBIDDEN_WORDS = (
    "buy",
    "sell",
    "execute",
    "place order",
    "trade now",
    "지금 사라",
    "지금 팔아라",
    "매수",
    "매도",
)


def _client() -> TestClient:
    return TestClient(create_app())


def test_system_ops_get_returns_full_payload() -> None:
    response = _client().get("/api/system-ops")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "protocols",
        "dataSources",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert {p["key"] for p in body["protocols"]} == _PROTOCOL_KEYS


def test_system_ops_protocols_have_camelcase_fields() -> None:
    body = _client().get("/api/system-ops").json()
    expected_fields = {
        "key",
        "title",
        "description",
        "idempotencyNote",
        "buttonLabel",
        "confirmLabel",
        "tone",
    }
    for protocol in body["protocols"]:
        assert expected_fields.issubset(protocol.keys()), protocol


def test_system_ops_data_sources_use_safe_status_values() -> None:
    body = _client().get("/api/system-ops").json()
    assert len(body["dataSources"]) >= 3
    for pill in body["dataSources"]:
        assert pill["status"] in {"LIVE", "FIXTURE", "MISSING"}


def test_system_ops_safety_caption_excludes_trading() -> None:
    body = _client().get("/api/system-ops").json()
    caption = body["safetyCaption"].lower()
    assert "operational" in caption
    assert "no trading" in caption


def test_system_ops_payload_contains_no_forbidden_wording() -> None:
    raw = json.dumps(_client().get("/api/system-ops").json()).lower()
    for forbidden in _FORBIDDEN_WORDS:
        assert forbidden not in raw, (
            f"System Ops payload leaks forbidden wording: {forbidden!r}"
        )


def test_system_ops_post_endpoints_return_structured_json() -> None:
    client = _client()
    for path, expected_key in _POST_ENDPOINTS:
        response = client.post(path)
        # Response is always JSON — never HTML, never a 5xx with a
        # raw stack trace.
        assert response.status_code == 200, (
            f"{path} responded {response.status_code}: {response.text}"
        )
        assert response.headers["content-type"].startswith("application/json")
        body = response.json()
        assert body["protocol"] == expected_key
        assert body["status"] in {"OK", "NOOP", "ERROR"}
        assert "message" in body and isinstance(body["message"], str)
        assert "ranAt" in body and body["ranAt"]
        # No raw stack-trace material in the message.
        for marker in ("Traceback", "File \"", "line "):
            assert marker not in body["message"], (
                f"{path} message contains stack-trace marker {marker!r}"
            )


def test_system_ops_post_endpoints_use_safe_messages() -> None:
    client = _client()
    for path, _ in _POST_ENDPOINTS:
        body = client.post(path).json()
        blob = (body["message"] + " " + body.get("detail", "")).lower()
        for forbidden in _FORBIDDEN_WORDS:
            assert forbidden not in blob, (
                f"{path} message leaks forbidden wording: {forbidden!r}"
            )


def test_use_fixture_header_is_accepted_on_system_ops() -> None:
    response = _client().get(
        "/api/system-ops", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"
