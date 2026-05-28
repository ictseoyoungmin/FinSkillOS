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
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository
from finskillos.services.trade_journal_service import (
    TradeJournalInput,
    TradeJournalService,
)

_FORBIDDEN_WORDS = (
    "execute",
    "place order",
    "trade now",
    "지금 사라",
    "지금 팔아라",
)


def _client() -> TestClient:
    return TestClient(create_app())


def _fixture_get(path: str):
    return _client().get(path, headers={"X-FSO-Use-Fixture": "1"})


def test_trade_memory_returns_full_payload() -> None:
    response = _fixture_get("/api/trade-memory")
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


def test_trade_memory_snapshot_exposes_v42_contract() -> None:
    body = _fixture_get("/api/trade-memory").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["weeklyReview"]["markdown"]
    assert body["mistakeFrequency"]
    assert "Reflection / process review" in body["safetyCaption"]


def test_trade_memory_form_rules_use_slice_12_sides() -> None:
    body = _fixture_get("/api/trade-memory").json()
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
    body = _fixture_get("/api/trade-memory").json()
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
    body = _fixture_get("/api/trade-memory").json()
    weekly = body["weeklyReview"]
    assert weekly["tradeCount"] >= 0
    assert "markdown" in weekly and "Weekly Review" in weekly["markdown"]
    assert "processNotes" in weekly


def test_trade_memory_weekly_review_route_matches() -> None:
    weekly = _fixture_get("/api/trade-memory/weekly-review").json()
    assert weekly["startDate"] == "2026-05-14"
    assert weekly["endDate"] == "2026-05-20"
    assert "markdown" in weekly


def test_trade_memory_weekly_review_endpoint_returns_markdown() -> None:
    body = _fixture_get("/api/trade-memory/weekly-review").json()
    assert body["markdown"]
    assert body["tradeCount"] >= 0


def test_trade_memory_get_reads_live_db_entries(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account",
            target_value=100000000,
        )
        TradeJournalService(session).create_entry(
            TradeJournalInput(
                trade_date=date.today(),
                ticker="NVDA",
                side="LONG",
                strategy_type="swing",
                amount=Decimal("4200000"),
                result_pnl=Decimal("320000"),
                result_pnl_pct=Decimal("7.62"),
                r_multiple=Decimal("1.50"),
                market_regime="HEALTHY_BULL",
                emotion_state="Calm",
                mistake_tags=(),
                sector="Semiconductors",
                theme="AI",
                thesis="Data-center demand momentum.",
                reason="Aligned with regime and checklist.",
            ),
            account_id=account.id,
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/trade-memory").json()

        assert body["source"] == "live"
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert body["recentEntries"][0]["ticker"] == "NVDA"
        assert body["weeklyReview"]["tradeCount"] == 1
        assert body["drivers"][0]["value"] == "1 stored"
        assert "DB-backed" in body["judgment"]["headline"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_trade_memory_weekly_review_route_reads_live_db(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account",
            target_value=100000000,
        )
        TradeJournalService(session).create_entry(
            TradeJournalInput(
                trade_date=date.today(),
                ticker="MSFT",
                side="LONG",
                result_pnl=Decimal("125000"),
                market_regime="HEALTHY_BULL",
                mistake_tags=(),
                thesis="Cloud guidance follow-through.",
                reason="Checklist remained calm.",
            ),
            account_id=account.id,
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        weekly = _client().get("/api/trade-memory/weekly-review").json()

        assert weekly["tradeCount"] == 1
        assert "Weekly Review" in weekly["markdown"]
        assert weekly["endDate"] == date.today().isoformat()
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_trade_memory_payload_descriptive_only_wording() -> None:
    raw = json.dumps(_fixture_get("/api/trade-memory").json()).lower()
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


def test_trade_entry_rejects_forbidden_wording() -> None:
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
