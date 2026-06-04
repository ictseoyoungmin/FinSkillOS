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
import uuid
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


def test_trade_memory_live_error_state_does_not_fall_back_to_fixture(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "trade-error.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    def _boom(session):  # noqa: ANN001
        raise RuntimeError("journal read failed")

    monkeypatch.setattr("api.routes.trade_memory._live_trade_memory_payload", _boom)

    try:
        body = _client().get("/api/trade-memory").json()
        assert body["source"] == "live"
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert body["systemStatus"]["db"] == "LIVE"
        assert "RuntimeError" in body["judgment"]["headline"]
        assert body["recentEntries"] == []

        weekly = _client().get("/api/trade-memory/weekly-review").json()
        assert weekly["tradeCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


# ---------------------------------------------------------------------------
# Slice 99 — entry edit / delete / CSV export
# ---------------------------------------------------------------------------


def _seed_live_entry(tmp_path, *, ticker: str = "NVDA"):
    """Create a sqlite DB with one account + one journal entry.

    Returns ``(engine, database_url, entry_id)`` so the caller can point the
    app at it via ``DATABASE_URL`` and address the stored entry by id."""

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
        trade = TradeJournalService(session).create_entry(
            TradeJournalInput(
                trade_date=date.today(),
                ticker=ticker,
                side="LONG",
                amount=Decimal("4200000"),
                market_regime="HEALTHY_BULL",
                mistake_tags=(),
                thesis="Data-center demand momentum.",
                reason="Aligned with regime and checklist.",
            ),
            account_id=account.id,
        )
        session.commit()
        entry_id = str(trade.id)
    return engine, database_url, entry_id


def test_put_trade_entry_updates_live_db(monkeypatch, tmp_path) -> None:
    engine, database_url, entry_id = _seed_live_entry(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        response = _client().put(
            f"/api/trade-memory/entries/{entry_id}",
            json={
                "tradeDate": date.today().isoformat(),
                "ticker": "AMD",
                "side": "LONG",
                "notes": "Revised the calm-process note.",
                "mistakeTags": [],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "OK"
        assert body["detail"] == "entry_updated"

        snapshot = _client().get("/api/trade-memory").json()
        assert snapshot["recentEntries"][0]["ticker"] == "AMD"
        assert snapshot["recentEntries"][0]["notes"] == "Revised the calm-process note."
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_put_trade_entry_rejects_invalid_entry_id() -> None:
    response = _client().put(
        "/api/trade-memory/entries/not-a-uuid",
        json={
            "tradeDate": date.today().isoformat(),
            "ticker": "AMD",
            "side": "LONG",
            "mistakeTags": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "invalid_entry_id"


def test_put_trade_entry_rejects_forbidden_wording() -> None:
    response = _client().put(
        f"/api/trade-memory/entries/{uuid.uuid4()}",
        json={
            "tradeDate": date.today().isoformat(),
            "ticker": "TSLA",
            "side": "LONG",
            "notes": "지금 사라",
            "mistakeTags": [],
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_delete_trade_entry_removes_live_db(monkeypatch, tmp_path) -> None:
    engine, database_url, entry_id = _seed_live_entry(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        response = _client().delete(f"/api/trade-memory/entries/{entry_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "OK"
        assert body["detail"] == "entry_deleted"

        snapshot = _client().get("/api/trade-memory").json()
        assert snapshot["recentEntries"] == []
        assert snapshot["weeklyReview"]["tradeCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_delete_trade_entry_missing_row_rejected(monkeypatch, tmp_path) -> None:
    engine, database_url, _entry_id = _seed_live_entry(tmp_path)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        response = _client().delete(f"/api/trade-memory/entries/{uuid.uuid4()}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "REJECTED"
        assert body["detail"] == "validation_error"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_export_trade_memory_csv_fixture() -> None:
    response = _client().get(
        "/api/trade-memory/export.csv", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    lines = response.text.splitlines()
    assert lines[0].startswith("trade_date,ticker,side,")
    assert len(lines) > 1


def test_export_trade_memory_csv_live(monkeypatch, tmp_path) -> None:
    engine, database_url, _entry_id = _seed_live_entry(tmp_path, ticker="NVDA")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        response = _client().get("/api/trade-memory/export.csv")
        assert response.status_code == 200
        body = response.text
        assert "NVDA" in body
        for forbidden in _FORBIDDEN_WORDS:
            assert forbidden not in body.lower()
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


# --- Slice 161: weekly-review period navigation (?as_of=) -------------------


def test_weekly_review_as_of_targets_a_past_window(monkeypatch, tmp_path) -> None:
    from datetime import timedelta

    db_path = tmp_path / "weekly-asof.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    today = date.today()
    last_week = today - timedelta(days=10)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account", target_value=100000000,
        )
        service = TradeJournalService(session)
        service.create_entry(
            TradeJournalInput(
                trade_date=today, ticker="NVDA", side="LONG",
                amount=Decimal("1000000"), mistake_tags=(),
            ),
            account_id=account.id,
        )
        service.create_entry(
            TradeJournalInput(
                trade_date=last_week, ticker="AAPL", side="LONG",
                amount=Decimal("500000"), mistake_tags=(),
            ),
            account_id=account.id,
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        # Default window (ending today) sees only the recent entry.
        default = client.get("/api/trade-memory/weekly-review").json()
        assert default["tradeCount"] == 1
        assert default["endDate"] == today.isoformat()

        # as_of points the 7-day window at the older entry.
        past = client.get(
            f"/api/trade-memory/weekly-review?as_of={last_week.isoformat()}"
        ).json()
        assert past["tradeCount"] == 1
        assert past["endDate"] == last_week.isoformat()
        assert past["startDate"] == (last_week - timedelta(days=6)).isoformat()
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_weekly_review_invalid_as_of_falls_back_to_current(
    monkeypatch, tmp_path
) -> None:
    engine, database_url = _empty_live_db(tmp_path, "weekly-badasof.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        body = _client().get(
            "/api/trade-memory/weekly-review?as_of=not-a-date"
        ).json()
        assert body["endDate"] == date.today().isoformat()
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


# --- Slice 160: trade CSV import (dry-run → confirm, append-only) -----------


def _empty_live_db(tmp_path, name: str = "trade-import.db"):
    """Create a sqlite DB with one account and no journal entries."""
    db_path = tmp_path / name
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        AccountRepository(session).create(
            name="Main Trading Account", target_value=100000000,
        )
        session.commit()
    return engine, database_url


_VALID_TRADE_CSV = (
    "trade_date,ticker,side,amount,market_regime,reason\n"
    "2026-05-01,NVDA,LONG,4200000,HEALTHY_BULL,Aligned with checklist.\n"
    "2026-05-02,AAPL,SHORT,1500000,DISTRIBUTION,Process review entry.\n"
)


def test_import_trade_preview_does_not_mutate(monkeypatch, tmp_path) -> None:
    engine, database_url = _empty_live_db(tmp_path, "ti-preview.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        csv_text = _VALID_TRADE_CSV + "bad-date,MSFT,LONG,5,,\n"
        result = client.post(
            "/api/trade-memory/import", json={"csvText": csv_text}
        ).json()
        assert result["status"] == "PREVIEW"
        assert result["valid"] == 2
        assert result["invalid"] == 1
        assert result["totalRows"] == 3
        flagged = [r for r in result["rows"] if r["status"] == "INVALID"]
        assert flagged and "trade_date" in flagged[0]["error"]

        # Nothing written.
        assert client.get("/api/trade-memory").json()["recentEntries"] == []
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_trade_confirm_appends(monkeypatch, tmp_path) -> None:
    engine, database_url = _empty_live_db(tmp_path, "ti-apply.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        result = client.post(
            "/api/trade-memory/import?confirm=true",
            json={"csvText": _VALID_TRADE_CSV},
        ).json()
        assert result["status"] == "APPLIED"
        assert result["valid"] == 2

        tickers = {
            e["ticker"]
            for e in client.get("/api/trade-memory").json()["recentEntries"]
        }
        assert {"NVDA", "AAPL"} <= tickers
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_trade_confirm_rejects_when_any_row_invalid(
    monkeypatch, tmp_path
) -> None:
    engine, database_url = _empty_live_db(tmp_path, "ti-atomic.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        csv_text = _VALID_TRADE_CSV + "2026-05-03,TSLA,NONSENSE,5,,\n"
        result = client.post(
            "/api/trade-memory/import?confirm=true",
            json={"csvText": csv_text},
        ).json()
        assert result["status"] == "ERROR"
        assert result["invalid"] == 1
        # Atomic: the two valid rows were NOT written.
        assert client.get("/api/trade-memory").json()["recentEntries"] == []
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_trade_flags_forbidden_wording(monkeypatch, tmp_path) -> None:
    engine, database_url = _empty_live_db(tmp_path, "ti-safety.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        csv_text = "trade_date,ticker,side,notes\n2026-05-01,TSLA,LONG,지금 사라\n"
        result = client.post(
            "/api/trade-memory/import", json={"csvText": csv_text}
        ).json()
        assert result["status"] == "PREVIEW"
        assert result["invalid"] == 1
        assert result["rows"][0]["status"] == "INVALID"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
