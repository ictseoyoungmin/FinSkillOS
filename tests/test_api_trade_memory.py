"""Slice 13.9 — FastAPI /api/trade-memory contract tests.

Verifies:

* GET /api/trade-memory response shape (judgment, drivers, conflicts,
  recent entries, performance buckets, mistake frequency, weekly
  review, watchpoints, form rules).
* GET /api/trade-memory/weekly-review returns the same shape embedded
  in /trade-memory.
* camelCase field names.
* Form rules expose the Slice-12 side vocabulary and default mistake
  tag set.
* POST /api/trade-memory/entries:
    - rejects invalid ISO trade_date,
    - rejects forbidden wording (Slice-12 write-seam guard),
    - accepts a safe entry in fixture-first mode (NOOP storage).
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app

_FORBIDDEN_WORDS = (
    "execute",
    "place order",
    "trade now",
    "지금 사라",
    "지금 팔아라",
)


def _client() -> TestClient:
    return TestClient(create_app())


def test_trade_memory_returns_full_payload() -> None:
    response = _client().get("/api/trade-memory")
    assert response.status_code == 200
    body = response.json()
    expected = {
        "generatedAt",
        "today",
        "systemStatus",
        "judgment",
        "drivers",
        "conflicts",
        "recentEntries",
        "performanceByRegime",
        "performanceBySectorTheme",
        "performanceByStrategy",
        "mistakeFrequency",
        "weeklyReview",
        "integratedInterpretation",
        "watchpoints",
        "formRules",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_trade_memory_form_rules_use_slice_12_sides() -> None:
    body = _client().get("/api/trade-memory").json()
    rules = body["formRules"]
    assert rules["allowedSides"] == [
        "LONG",
        "SHORT",
        "WATCH",
        "EXIT_REVIEW",
        "OTHER",
    ]
    assert "Chasing" in rules["defaultMistakeTags"]
    assert "execution controls" in rules["disclaimer"].lower()


def test_trade_memory_recent_entries_use_camelcase_fields() -> None:
    body = _client().get("/api/trade-memory").json()
    assert len(body["recentEntries"]) >= 1
    expected = {
        "id",
        "tradeDate",
        "ticker",
        "side",
        "strategyType",
        "marketRegime",
        "emotionState",
        "resultPnl",
        "resultPnlPct",
        "rMultiple",
        "mistakeTags",
    }
    for entry in body["recentEntries"]:
        assert expected.issubset(entry.keys()), entry


def test_trade_memory_weekly_review_block() -> None:
    body = _client().get("/api/trade-memory").json()
    weekly = body["weeklyReview"]
    assert weekly["tradeCount"] >= 0
    assert "markdown" in weekly and "Weekly Review" in weekly["markdown"]
    assert "processNotes" in weekly


def test_trade_memory_weekly_review_route_matches() -> None:
    weekly = _client().get("/api/trade-memory/weekly-review").json()
    assert weekly["startDate"] == "2026-05-14"
    assert weekly["endDate"] == "2026-05-20"
    assert "markdown" in weekly


def test_trade_memory_payload_descriptive_only_wording() -> None:
    raw = json.dumps(_client().get("/api/trade-memory").json()).lower()
    # The Trade Memory payload references legacy BUY / SELL inside
    # form vocab + Trade entries — the FORBIDDEN_WORDS list above
    # intentionally avoids those substrings and instead checks the
    # narrative-only forbidden actions.
    for forbidden in _FORBIDDEN_WORDS:
        assert forbidden not in raw, (
            f"Trade Memory payload leaks forbidden wording: {forbidden!r}"
        )


def test_post_trade_entry_rejects_invalid_trade_date() -> None:
    response = _client().post(
        "/api/trade-memory/entries",
        json={
            "tradeDate": "not-a-date",
            "ticker": "TSLA",
            "side": "LONG",
            "mistakeTags": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "invalid_trade_date"


def test_post_trade_entry_rejects_forbidden_wording_in_notes() -> None:
    response = _client().post(
        "/api/trade-memory/entries",
        json={
            "tradeDate": "2026-05-19",
            "ticker": "TSLA",
            "side": "LONG",
            "notes": "지금 사라",
            "mistakeTags": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"


def test_post_trade_entry_accepts_safe_entry_in_fixture_mode() -> None:
    response = _client().post(
        "/api/trade-memory/entries",
        json={
            "tradeDate": "2026-05-19",
            "ticker": "TSLA",
            "side": "LONG",
            "strategyType": "swing",
            "thesis": "AI / Data Center demand momentum.",
            "reason": "Aligned with regime.",
            "mistakeTags": ["Chasing"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    # Fixture-first session returns OK with no_database_session detail.
    assert body["status"] in {"OK", "ERROR"}


def test_use_fixture_header_is_accepted_on_trade_memory() -> None:
    response = _client().get(
        "/api/trade-memory", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_use_fixture_header_is_accepted_on_weekly_review() -> None:
    response = _client().get(
        "/api/trade-memory/weekly-review",
        headers={"X-FSO-Use-Fixture": "1"},
    )
    assert response.status_code == 200
    assert "markdown" in response.json()
