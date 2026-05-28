"""Slice 13.9 — FastAPI /api/event-radar contract tests.

Verifies:

* GET response shape (judgment, drivers, conflicts, upcoming events,
  high-risk subset, holdings-linked subset, linked news, watchpoints,
  date-status badge tone map).
* camelCase field names.
* Date-status badge tone map covers the five Slice-11 statuses with
  the expected colour buckets.
* Event Radar remains read-only. Event seeding lives in System Ops.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)

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
        "dataState",
        "judgment",
        "drivers",
        "conflicts",
        "upcoming",
        "highRisk",
        "holdingsLinked",
        "linkedNews",
        "integratedInterpretation",
        "watchpoints",
        "dateStatusBadgeTone",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    if body["source"] == "fixture":
        assert body["generatedAt"] == FIXTURE_TIMESTAMP
        assert body["dataState"]["calendarStatus"] == "fixture_first"
    else:
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert body["dataState"]["calendarStatus"] in {"db_backed", "empty"}
    assert body["dataState"]["dateConfidenceStatus"] in {
        "confirmed",
        "mixed",
        "uncertain",
        "missing",
    }


def test_event_radar_snapshot_exposes_v42_contract() -> None:
    body = _client().get("/api/event-radar").json()

    assert body["judgment"]
    assert body["dataState"]["eventCount"] == len(body["upcoming"])
    assert body["dataState"]["linkedNewsCount"] == len(body["linkedNews"])
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
    body = _client().get(
        "/api/event-radar", headers={"X-FSO-Use-Fixture": "1"}
    ).json()
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


def test_event_radar_does_not_expose_mutation_routes() -> None:
    spec = _client().get("/openapi.json").json()
    paths = set(spec.get("paths", {}).keys())
    assert "/api/event-radar/manual-event" not in paths
    assert "/api/event-radar/seed-sample-events" not in paths
    assert "/api/system-ops/seed-sample-events" in paths


def test_use_fixture_header_is_accepted_on_event_radar() -> None:
    response = _client().get(
        "/api/event-radar", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_event_radar_can_return_live_db_read_model(monkeypatch, tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'event_radar.db'}"
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    reset_settings_cache()

    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        EventService(session).create_event(
            EventInput(
                title="NVIDIA earnings window",
                event_type="EARNINGS",
                date_status="TENTATIVE",
                start_date=date(2026, 6, 10),
                source="Nasdaq",
                description="Tentative earnings window.",
                importance_score=Decimal("4.0"),
            ),
            links=(
                EventLinkInput(ticker="NVDA", theme="AI", event_key="EARNINGS"),
            ),
        )
        session.commit()

    try:
        response = TestClient(create_app()).get("/api/event-radar")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "live"
        assert body["dataState"]["calendarStatus"] == "db_backed"
        assert body["dataState"]["eventCount"] == 1
        assert body["dataState"]["dateConfidenceStatus"] == "uncertain"
        assert body["upcoming"][0]["title"] == "NVIDIA earnings window"
    finally:
        reset_settings_cache()
        engine.dispose()


def test_event_radar_live_empty_db_is_explicit(monkeypatch, tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'empty_event_radar.db'}"
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db_url)
    reset_settings_cache()

    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)

    try:
        response = TestClient(create_app()).get("/api/event-radar")
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "live"
        assert body["dataState"]["calendarStatus"] == "empty"
        assert body["dataState"]["eventCount"] == 0
        assert body["upcoming"] == []
    finally:
        reset_settings_cache()
        engine.dispose()
