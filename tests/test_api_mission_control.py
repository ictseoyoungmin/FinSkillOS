"""Slice 13.8 — FastAPI /api/mission-control contract tests."""

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
from finskillos.services.portfolio_service import (
    PortfolioPositionInput,
    PortfolioService,
)


def _client() -> TestClient:
    return TestClient(create_app())


def _fixture_get(client: TestClient):
    return client.get("/api/mission-control", headers={"X-FSO-Use-Fixture": "1"})


def test_mission_control_returns_full_payload() -> None:
    response = _fixture_get(_client())
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "goal",
        "milestones",
        "portfolio",
        "capitalMap",
        "themeMap",
        "challengeStatusCaption",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_mission_control_goal_has_camelcase_fields() -> None:
    body = _fixture_get(_client()).json()
    goal = body["goal"]
    expected = {
        "currentValue",
        "targetValue",
        "remainingValue",
        "progressPct",
        "progressRatio",
        "goalMode",
        "earlyStopTriggered",
        "phase",
        "challengeLabel",
    }
    assert expected.issubset(goal.keys())
    # Strings (Decimal -> string) for arithmetic safety on the React side.
    assert float(goal["progressPct"]) == 73.4


def test_mission_control_milestones_cover_quarter_steps() -> None:
    body = _fixture_get(_client()).json()
    milestones = body["milestones"]
    pcts = [m["pct"] for m in milestones]
    assert pcts == [25, 50, 75, 100]
    for milestone in milestones:
        assert milestone["state"] in {"COMPLETED", "APPROACHING", "PENDING"}


def test_mission_control_portfolio_snapshot_fields_present() -> None:
    body = _fixture_get(_client()).json()
    snapshot = body["portfolio"]
    expected = {
        "totalValue",
        "cashValue",
        "positionCount",
        "largestPositionTicker",
        "largestPositionWeightPct",
        "overSingleLimitTickers",
    }
    assert expected.issubset(snapshot.keys())
    assert snapshot["positionCount"] >= 1


def test_mission_control_capital_map_has_descriptive_tones() -> None:
    body = _fixture_get(_client()).json()
    tones = {slice_["tone"] for slice_ in body["capitalMap"]}
    assert tones.issubset({"info", "warning", "danger", "neutral", "success"})


def test_mission_control_challenge_caption_mentions_challenge() -> None:
    body = _fixture_get(_client()).json()
    caption = body["challengeStatusCaption"].lower()
    assert "challenge" in caption


def test_mission_control_does_not_expose_execution_concepts() -> None:
    raw = json.dumps(_fixture_get(_client()).json()).lower()
    for forbidden in ('"buy"', '"sell"', '"execute"', '"order"', '"place_order"'):
        assert forbidden not in raw, (
            f"Mission Control response leaks execution concept {forbidden!r}"
        )


def test_use_fixture_header_is_accepted_on_mission_control() -> None:
    response = _client().get(
        "/api/mission-control", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_mission_control_reads_live_db_snapshot(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "mission.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account",
            target_value=Decimal("100000000"),
        )
        PortfolioService(session).import_snapshot(
            account_id=account.id,
            snapshot_date=date(2026, 5, 27),
            cash_value=Decimal("5000000"),
            rows=[
                PortfolioPositionInput(
                    ticker="NVDA",
                    quantity=Decimal("10"),
                    market_value=Decimal("25000000"),
                    sector="Semiconductors",
                    theme="AI Infrastructure",
                ),
                PortfolioPositionInput(
                    ticker="AAPL",
                    quantity=Decimal("8"),
                    market_value=Decimal("10000000"),
                    sector="Technology",
                    theme="Mega Cap Tech",
                ),
            ],
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().get("/api/mission-control")
        body = response.json()

        assert response.status_code == 200
        assert body["source"] == "live"
        assert body["goal"]["currentValue"] == "40000000.00"
        assert body["goal"]["progressPct"] == "40.00"
        assert body["portfolio"]["positionCount"] == 2
        assert body["portfolio"]["largestPositionTicker"] == "NVDA"
        assert body["capitalMap"][0]["label"] == "Semiconductors"
        assert body["themeMap"][0]["label"] == "AI Infrastructure"
        # import_snapshot derives total = positions + cash → reconciliation OK.
        assert body["reconciliation"]["status"] == "OK"
        assert body["reconciliation"]["snapshotTotal"] == "40000000.00"
        assert body["reconciliation"]["positionsValue"] == "35000000.00"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_mission_control_reconciliation_flags_mismatch(monkeypatch, tmp_path) -> None:
    # Slice 157: a snapshot total that doesn't equal positions + cash is flagged.
    db_path = tmp_path / "mission.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    from finskillos.db.repositories import PortfolioRepository, PositionRepository

    with factory() as session:
        account = AccountRepository(session).create(
            name="Main Trading Account", target_value=Decimal("100000000"),
        )
        # Stored baseline says 100M, but positions + cash only sum to 30M.
        PortfolioRepository(session).create_snapshot(
            account_id=account.id, snapshot_date=date(2026, 5, 27),
            total_value=Decimal("100000000"), cash_value=Decimal("5000000"),
        )
        PositionRepository(session).create(
            account_id=account.id, ticker="NVDA", quantity=Decimal("10"),
            market_value=Decimal("25000000"),
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/mission-control").json()
        rec = body["reconciliation"]
        assert rec["status"] == "MISMATCH"
        assert rec["snapshotTotal"] == "100000000.00"
        assert rec["reconciledTotal"] == "30000000.00"
        assert rec["drift"] == "70000000.00"
        assert "off by" in rec["detail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_mission_control_live_empty_state_stays_live(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "mission-empty.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().get("/api/mission-control")
        body = response.json()

        assert response.status_code == 200
        assert body["source"] == "live"
        assert body["systemStatus"]["db"] == "LIVE"
        assert body["portfolio"]["positionCount"] == 0
        assert body["capitalMap"] == []
        assert body["themeMap"] == []
        assert "baseline" in body["challengeStatusCaption"].lower()
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_mission_control_live_error_state_does_not_fall_back_to_fixture(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "mission-error.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    def _boom(session):  # noqa: ANN001
        raise RuntimeError("mission read failed")

    monkeypatch.setattr(
        "api.routes.mission_control._build_live_mission_control", _boom
    )

    try:
        body = _client().get("/api/mission-control").json()
        assert body["source"] == "live"
        assert body["generatedAt"] != FIXTURE_TIMESTAMP
        assert body["systemStatus"]["db"] == "LIVE"
        assert "RuntimeError" in body["judgment"]["summary"]
        assert body["capitalMap"] == []
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


# --- Slice 158: portfolio manual entry / edit (CRUD) ------------------------


def _live_db(tmp_path, name: str):
    """Create a fresh sqlite engine for a mutation test."""
    db_path = tmp_path / name
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return engine, database_url


def _seed_account(engine) -> None:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        AccountRepository(session).create(
            name="Main Trading Account", target_value=Decimal("100000000"),
        )
        session.commit()


def test_create_position_appends_holding(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-create.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        resp = client.post(
            "/api/mission-control/positions",
            json={
                "ticker": "nvda",
                "quantity": "10",
                "marketValue": "25000000",
                "sector": "Semiconductors",
                "theme": "AI Infrastructure",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "live"
        assert body["portfolio"]["positionCount"] == 1
        rows = body["positions"]
        assert len(rows) == 1
        assert rows[0]["ticker"] == "NVDA"  # upper-cased
        assert rows[0]["marketValue"] == "25000000.00"
        assert rows[0]["id"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_create_position_bootstraps_account_when_empty(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-bootstrap.db")
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        resp = _client().post(
            "/api/mission-control/positions",
            json={"ticker": "AAPL", "quantity": "5", "marketValue": "10000000"},
        )
        assert resp.status_code == 200
        assert resp.json()["positions"][0]["ticker"] == "AAPL"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_update_position_edits_in_place(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-update.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        created = client.post(
            "/api/mission-control/positions",
            json={"ticker": "NVDA", "quantity": "10", "marketValue": "25000000"},
        ).json()
        pos_id = created["positions"][0]["id"]

        resp = client.put(
            f"/api/mission-control/positions/{pos_id}",
            json={
                "ticker": "NVDA",
                "quantity": "12",
                "marketValue": "30000000",
                "theme": "AI Infrastructure",
            },
        )
        assert resp.status_code == 200
        row = resp.json()["positions"][0]
        assert Decimal(row["quantity"]) == Decimal("12")
        assert row["marketValue"] == "30000000.00"
        assert row["theme"] == "AI Infrastructure"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_update_missing_position_returns_404(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-update-404.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        resp = _client().put(
            "/api/mission-control/positions/00000000-0000-0000-0000-000000000000",
            json={"ticker": "NVDA", "quantity": "1", "marketValue": "1000"},
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "position_not_found"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_delete_position_removes_holding(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-delete.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        created = client.post(
            "/api/mission-control/positions",
            json={"ticker": "NVDA", "quantity": "10", "marketValue": "25000000"},
        ).json()
        pos_id = created["positions"][0]["id"]

        resp = client.delete(f"/api/mission-control/positions/{pos_id}")
        assert resp.status_code == 200
        assert resp.json()["positions"] == []
        assert resp.json()["portfolio"]["positionCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_clear_positions_removes_all(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-clear.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        for tk in ("NVDA", "AAPL", "MSFT"):
            client.post(
                "/api/mission-control/positions",
                json={"ticker": tk, "quantity": "1", "marketValue": "1000000"},
            )
        resp = client.post("/api/mission-control/clear-positions")
        assert resp.status_code == 200
        assert resp.json()["positions"] == []
        assert resp.json()["portfolio"]["positionCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_export_positions_csv_round_trips(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-export.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        client.post(
            "/api/mission-control/positions",
            json={
                "ticker": "NVDA",
                "quantity": "10",
                "marketValue": "25000000",
                "sector": "Semiconductors",
            },
        )
        resp = client.get("/api/mission-control/positions/export.csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        body = resp.text
        assert body.splitlines()[0].startswith("ticker,quantity,market_value")
        assert "NVDA" in body

        # Re-importing the export is a pure UPDATE (round-trip, non-destructive).
        preview = client.post(
            "/api/mission-control/import-positions",
            json={"csvText": body},
        ).json()
        assert preview["status"] == "PREVIEW"
        assert preview["updates"] == 1
        assert preview["adds"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_dry_run_does_not_mutate(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-import-dry.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        csv_text = (
            "ticker,quantity,market_value,sector\n"
            "NVDA,10,25000000,Semiconductors\n"
            "AAPL,8,10000000,Technology\n"
        )
        preview = client.post(
            "/api/mission-control/import-positions",
            json={"csvText": csv_text},
        ).json()
        assert preview["status"] == "PREVIEW"
        assert preview["adds"] == 2
        assert preview["totalRows"] == 2
        assert preview["snapshot"] is None
        assert {r["ticker"] for r in preview["rows"]} == {"NVDA", "AAPL"}

        # Nothing was written.
        body = client.get("/api/mission-control").json()
        assert body["portfolio"]["positionCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_confirm_applies_upsert(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-import-apply.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        # Pre-existing NVDA that the CSV will update; AAPL is new.
        client.post(
            "/api/mission-control/positions",
            json={"ticker": "NVDA", "quantity": "5", "marketValue": "12000000"},
        )
        csv_text = (
            "ticker,quantity,market_value\n"
            "NVDA,10,25000000\n"
            "AAPL,8,10000000\n"
        )
        result = client.post(
            "/api/mission-control/import-positions?confirm=true",
            json={"csvText": csv_text},
        ).json()
        assert result["status"] == "APPLIED"
        assert result["adds"] == 1
        assert result["updates"] == 1
        snap = result["snapshot"]
        assert snap["portfolio"]["positionCount"] == 2
        rows = {r["ticker"]: r for r in snap["positions"]}
        assert rows["NVDA"]["marketValue"] == "25000000.00"  # updated in place
        assert "AAPL" in rows
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_import_malformed_csv_reports_error(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-import-bad.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        bad = "ticker,quantity,market_value\nNVDA,not-a-number,25000000\n"
        result = client.post(
            "/api/mission-control/import-positions?confirm=true",
            json={"csvText": bad},
        ).json()
        assert result["status"] == "ERROR"
        assert result["parseErrors"]
        # Nothing applied.
        body = client.get("/api/mission-control").json()
        assert body["portfolio"]["positionCount"] == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_patch_snapshot_baseline_updates_reconciliation(monkeypatch, tmp_path) -> None:
    engine, database_url = _live_db(tmp_path, "mc-snapshot.db")
    _seed_account(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        client.post(
            "/api/mission-control/positions",
            json={"ticker": "NVDA", "quantity": "10", "marketValue": "25000000"},
        )
        # Set a baseline that matches positions + cash (25M + 0) → reconciliation OK.
        resp = client.patch(
            "/api/mission-control/snapshot",
            json={"totalValue": "25000000", "cashValue": "0"},
        )
        assert resp.status_code == 200
        rec = resp.json()["reconciliation"]
        assert rec["status"] == "OK"
        assert rec["snapshotTotal"] == "25000000.00"

        # Now drift the baseline → MISMATCH.
        resp2 = client.patch(
            "/api/mission-control/snapshot",
            json={"totalValue": "99000000"},
        )
        rec2 = resp2.json()["reconciliation"]
        assert rec2["status"] == "MISMATCH"
        assert rec2["snapshotTotal"] == "99000000.00"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
