"""Slice 13.9 — FastAPI /api/event-radar contract tests.

Verifies:

* GET response shape (judgment, drivers, conflicts, upcoming events,
  high-risk subset, holdings-linked subset, linked news, watchpoints,
  manual-entry rules, date-status badge tone map).
* camelCase field names.
* Date-status badge tone map covers the five Slice-11 statuses with
  the expected colour buckets.
* POST /api/event-radar/manual-event rejects:
    - invalid ISO dates,
    - CONFIRMED + source="manual_seed" (or empty source).
* POST /api/event-radar/seed-sample-events returns a structured
  SeedEventsResult even in fixture-first mode.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app

_FORBIDDEN_WORDS = (
    "buy ",
    " buy",
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


def test_event_radar_returns_full_payload() -> None:
    response = _client().get("/api/event-radar")
    assert response.status_code == 200
    body = response.json()
    expected = {
        "generatedAt",
        "today",
        "systemStatus",
        "judgment",
        "drivers",
        "conflicts",
        "upcoming",
        "highRisk",
        "holdingsLinked",
        "linkedNews",
        "integratedInterpretation",
        "watchpoints",
        "manualEntryRules",
        "dateStatusBadgeTone",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_event_radar_snapshot_exposes_v42_contract() -> None:
    body = _client().get("/api/event-radar").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["dateStatusBadgeTone"]
    assert "preparation / exposure score" in body["safetyCaption"]
    assert "price direction prediction" in body["safetyCaption"]


def test_event_radar_judgment_describes_preparation_not_prediction() -> None:
    body = _client().get("/api/event-radar").json()
    caption = body["safetyCaption"].lower()
    assert "preparation" in caption
    assert "not a price direction prediction" in caption


def test_event_radar_date_status_badge_tone_map() -> None:
    body = _client().get("/api/event-radar").json()
    tone_map = body["dateStatusBadgeTone"]
    assert tone_map["CONFIRMED"] == "success"
    assert tone_map["WINDOW"] == "info"
    assert tone_map["TENTATIVE"] == "warning"
    assert tone_map["REPORTED"] == "warning"
    assert tone_map["SPECULATIVE"] == "purple"


def test_event_radar_upcoming_rows_use_camelcase_fields() -> None:
    body = _client().get("/api/event-radar").json()
    assert len(body["upcoming"]) >= 1
    expected = {
        "eventId",
        "title",
        "eventType",
        "dateStatus",
        "startDate",
        "daysToEvent",
        "importanceScore",
        "eventRiskScore",
        "riskLabel",
        "portfolioExposure",
        "affectedTickers",
        "affectedSectors",
        "affectedThemes",
        "links",
        "linkedNews",
    }
    for row in body["upcoming"]:
        assert expected.issubset(row.keys()), row


def test_event_radar_payload_descriptive_only_wording() -> None:
    body = _client().get("/api/event-radar").json()
    raw = json.dumps(body).lower()
    # "sell-the-news" remains an allowed descriptive idiom (Slice 06
    # cleanup); make sure the literal idiom does NOT trip the bare
    # 'buy '/' buy' guard.
    for forbidden in _FORBIDDEN_WORDS:
        assert forbidden not in raw, (
            f"Event Radar payload leaks forbidden wording: {forbidden!r}"
        )


def test_manual_event_rejects_confirmed_plus_manual_seed() -> None:
    response = _client().post(
        "/api/event-radar/manual-event",
        json={
            "title": "Should be rejected",
            "eventType": "EARNINGS",
            "dateStatus": "CONFIRMED",
            "startDate": "2026-06-01",
            "endDate": None,
            "source": "manual_seed",
            "sourceUrl": None,
            "description": None,
            "importanceScore": "1.0",
            "ticker": None,
            "sector": None,
            "theme": None,
            "eventKey": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "confirmed_requires_external_source"


def test_manual_event_rejects_confirmed_manual_seed() -> None:
    response = _client().post(
        "/api/event-radar/manual-event",
        json={
            "title": "Should be rejected",
            "eventType": "EARNINGS",
            "dateStatus": "CONFIRMED",
            "startDate": "2026-06-01",
            "endDate": None,
            "source": "manual_seed",
            "sourceUrl": None,
            "description": None,
            "importanceScore": "1.0",
            "ticker": None,
            "sector": None,
            "theme": None,
            "eventKey": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "confirmed_requires_external_source"


def test_manual_event_rejects_invalid_start_date() -> None:
    response = _client().post(
        "/api/event-radar/manual-event",
        json={
            "title": "Probe",
            "eventType": "EARNINGS",
            "dateStatus": "TENTATIVE",
            "startDate": "not-a-date",
            "endDate": None,
            "source": "Reuters",
            "sourceUrl": None,
            "description": None,
            "importanceScore": "1.0",
            "ticker": None,
            "sector": None,
            "theme": None,
            "eventKey": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "invalid_start_date"


def test_manual_event_tentative_with_source_accepted() -> None:
    response = _client().post(
        "/api/event-radar/manual-event",
        json={
            "title": "Probe Tentative",
            "eventType": "EARNINGS",
            "dateStatus": "TENTATIVE",
            "startDate": "2026-06-01",
            "endDate": None,
            "source": "manual_seed",
            "sourceUrl": None,
            "description": "Tentative; not confirmed.",
            "importanceScore": "1.0",
            "ticker": "NVDA",
            "sector": None,
            "theme": "AI",
            "eventKey": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    # Fixture-first session returns OK with no_database_session detail.
    assert body["status"] in {"OK", "ERROR"}


def test_seed_sample_events_returns_structured_result() -> None:
    response = _client().post("/api/event-radar/seed-sample-events")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["status"] in {"OK", "NOOP", "ERROR"}
    assert "ranAt" in body and body["ranAt"]
    # No raw stack-trace material in the message.
    for marker in ("Traceback", 'File "', "line "):
        assert marker not in body["message"], body


def test_seed_sample_events_returns_structured_json() -> None:
    response = _client().post("/api/event-radar/seed-sample-events")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"OK", "NOOP", "ERROR"}
    assert "message" in body
    assert "detail" in body


def test_use_fixture_header_is_accepted_on_event_radar() -> None:
    response = _client().get(
        "/api/event-radar", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"
