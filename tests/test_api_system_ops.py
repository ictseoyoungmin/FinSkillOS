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
from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.db.repositories import (
    AccountRepository,
    EventRepository,
    IndicatorRepository,
    MarketRepository,
    NewsArticleRepository,
    PortfolioRepository,
    PositionRepository,
    SystemOpsProtocolRunRepository,
    SystemOpsSettingsRepository,
    WorkerCycleRunRepository,
    WorkerJobRepository,
)

_PROTOCOL_KEYS = {
    "seed_sample_account",
    "seed_system_folder",
    "refresh_news",
    "refresh_market_data",
    "calculate_indicators",
    "recompute_regime",
    "run_risk_guards",
    "seed_sample_events",
    "refresh_events",
}

_POST_ENDPOINTS = (
    ("/api/system-ops/seed-sample-account", "seed_sample_account"),
    ("/api/system-ops/seed-system-folder", "seed_system_folder"),
    ("/api/system-ops/refresh-news", "refresh_news"),
    ("/api/system-ops/refresh-market-data", "refresh_market_data"),
    ("/api/system-ops/calculate-indicators", "calculate_indicators"),
    ("/api/system-ops/recompute-regime", "recompute_regime"),
    ("/api/system-ops/run-risk-guards", "run_risk_guards"),
    ("/api/system-ops/seed-sample-events", "seed_sample_events"),
    ("/api/system-ops/refresh-events", "refresh_events"),
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


def _data_source_by_label(body: dict, label: str) -> dict:
    return next(item for item in body["dataSources"] if item["label"] == label)


def test_system_ops_get_returns_full_payload() -> None:
    response = _client().get("/api/system-ops")
    assert response.status_code == 200
    body = response.json()

    expected = {
        "generatedAt",
        "systemStatus",
        "protocols",
        "dataSources",
        "recentProtocolRuns",
        "workerStatus",
        "runtimeSettings",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP
    assert {p["key"] for p in body["protocols"]} == _PROTOCOL_KEYS
    assert body["workerStatus"]["status"] in {"OK", "NOOP", "ERROR", "MISSING"}


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


def test_system_ops_runtime_settings_get() -> None:
    response = _client().get("/api/system-ops/runtime-settings")
    assert response.status_code == 200
    body = response.json()
    assert {"values", "overrides", "capturedAt"}.issubset(body.keys())
    assert isinstance(body["values"], dict)


def test_system_ops_runtime_settings_get_applies_db_overrides(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_WORKER_INTERVAL_SECONDS", "111")
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "yahoo")
    reset_settings_cache()

    try:
        first = _client().get("/api/system-ops/runtime-settings").json()
        assert first["values"]["FINSKILLOS_WORKER_INTERVAL_SECONDS"] == "111"

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            SystemOpsSettingsRepository(session).patch(
                {
                    "FINSKILLOS_WORKER_INTERVAL_SECONDS": "222",
                    "FINSKILLOS_MARKET_REFRESH_ADAPTER": "mock",
                },
                updated_by="test",
            )
            session.commit()

        second = _client().get("/api/system-ops/runtime-settings").json()
        assert second["values"]["FINSKILLOS_WORKER_INTERVAL_SECONDS"] == "222"
        assert second["values"]["FINSKILLOS_MARKET_REFRESH_ADAPTER"] == "mock"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_runtime_settings_patch_persists_to_db(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().patch(
            "/api/system-ops/runtime-settings",
            json={
                "values": {
                    "FINSKILLOS_WORKER_INTERVAL_SECONDS": 333,
                    "FINSKILLOS_WORKER_MARKET_ENABLED": False,
                    "FINSKILLOS_REFRESH_FOLDER_NAMES": "Growth,Value",
                }
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["values"]["FINSKILLOS_WORKER_INTERVAL_SECONDS"] == "333"
        assert body["values"]["FINSKILLOS_WORKER_MARKET_ENABLED"] == "False"
        assert body["values"]["FINSKILLOS_REFRESH_FOLDER_NAMES"] == "Growth,Value"

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            row = SystemOpsSettingsRepository(session).get()
            assert row.values["FINSKILLOS_WORKER_INTERVAL_SECONDS"] == "333"
            assert row.values["FINSKILLOS_WORKER_MARKET_ENABLED"] == "False"
            assert row.values["FINSKILLOS_REFRESH_FOLDER_NAMES"] == "Growth,Value"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_runtime_settings_patch_rejects_invalid_key(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().patch(
            "/api/system-ops/runtime-settings",
            json={"values": {"BAD_SETTING": "1"}},
        )
        assert response.status_code == 400
        assert "Unsupported runtime setting key" in response.json()["detail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_runtime_settings_patch_stores_and_is_applied_in_refresh_job(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_MARKET_REFRESH_ADAPTER", "yahoo")
    reset_settings_cache()

    try:
        patch_response = _client().patch(
            "/api/system-ops/runtime-settings",
            json={
                "values": {
                    "FINSKILLOS_WORKER_INTERVAL_SECONDS": "222",
                    "FINSKILLOS_MARKET_REFRESH_ADAPTER": "mock",
                    "FINSKILLOS_NEWS_RSS_LANGUAGE": "de-DE",
                    "FINSKILLOS_REFRESH_FOLDER_NAMES": "Growth,Value",
                }
            },
        )
        assert patch_response.status_code == 200

        queue_response = _client().post("/api/system-ops/refresh-market-data").json()
        assert queue_response["protocol"] == "refresh_market_data"
        assert queue_response["status"] == "QUEUED"

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            job = WorkerJobRepository(session).list_recent(limit=1)[0]
            payload = job.payload or {}
            runtime_payload = payload.get("runtime_settings")
            assert isinstance(runtime_payload, dict)
            assert runtime_payload["FINSKILLOS_WORKER_INTERVAL_SECONDS"] == "222"
            assert runtime_payload["FINSKILLOS_MARKET_REFRESH_ADAPTER"] == "mock"
            assert runtime_payload["FINSKILLOS_NEWS_RSS_LANGUAGE"] == "de-DE"
            assert runtime_payload["FINSKILLOS_REFRESH_FOLDER_NAMES"] == "Growth,Value"
            assert payload["requested_from"] == "system_ops"
            assert job.requested_by == "system_ops"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_event_catalog_protocol_marks_ingestion_boundary() -> None:
    body = _client().get("/api/system-ops").json()
    protocol = next(
        item for item in body["protocols"] if item["key"] == "seed_sample_events"
    )

    assert protocol["title"] == "Seed event catalog"
    assert protocol["buttonLabel"] == "Seed event catalog"
    assert "System Ops ingestion boundary" in protocol["description"]
    assert "Catalyst Watch stays read-only" in protocol["description"]
    assert "CONFIRMED" not in protocol["idempotencyNote"]


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
        assert body["status"] in {"OK", "NOOP", "ERROR", "QUEUED"}
        assert "message" in body and isinstance(body["message"], str)
        assert "detailEvidence" in body
        assert isinstance(body["detailEvidence"], list)
        assert body["detailEvidence"]
        assert {"key", "value"}.issubset(body["detailEvidence"][0].keys())
        assert all(
            isinstance(item["key"], str) and isinstance(item["value"], str)
            for item in body["detailEvidence"]
        )
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
    body = response.json()
    assert body["source"] == "fixture"
    assert _data_source_by_label(body, "Database")["status"] == "FIXTURE"


def test_system_ops_live_data_sources_match_db_backed_payload(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/system-ops").json()

        assert body["source"] == "live"
        assert _data_source_by_label(body, "Database")["status"] == "LIVE"
        assert (
            _data_source_by_label(body, "Market / Indicators")["status"] == "LIVE"
        )
        assert (
            _data_source_by_label(body, "News / Event Stores")["status"] == "LIVE"
        )
        assert "DB-backed" in _data_source_by_label(body, "Database")["detail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_live_evidence_copy_matches_db_backed_payload(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/system-ops").json()
        raw = json.dumps(
            {
                "judgment": body["judgment"],
                "drivers": body["drivers"],
                "conflicts": body["conflicts"],
            }
        ).lower()

        assert body["source"] == "live"
        assert body["judgment"]["title"] == "Local System DB-Backed"
        assert next(
            driver for driver in body["drivers"] if driver["title"] == "Protocols"
        )["score"] == str(len(body["protocols"]))
        assert next(
            driver for driver in body["drivers"] if driver["title"] == "Data layer"
        )["score"] == "Live"
        assert "fixture-first" not in raw
        assert "source freshness is limited" not in raw
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_protocol_runs_are_audited_to_jsonl(monkeypatch, tmp_path) -> None:
    audit_path = tmp_path / "ops_runs.jsonl"
    monkeypatch.setenv("FINSKILLOS_SYSTEM_OPS_AUDIT_LOG", str(audit_path))

    client = _client()
    post_body = client.post("/api/system-ops/seed-sample-account").json()
    assert post_body["protocol"] == "seed_sample_account"

    assert audit_path.exists()
    audit_lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(audit_lines) == 1
    raw_record = json.loads(audit_lines[0])
    assert raw_record["protocol"] == "seed_sample_account"
    assert raw_record["status"] in {"OK", "NOOP", "ERROR"}
    assert raw_record["dbStatus"] in {"LIVE", "MISSING"}
    assert raw_record["source"] in {"fixture", "live"}

    get_body = client.get("/api/system-ops").json()
    assert get_body["recentProtocolRuns"][0]["protocol"] == "seed_sample_account"
    assert get_body["recentProtocolRuns"][0]["ranAt"] == post_body["ranAt"]


def test_fixture_mode_shows_deterministic_protocol_history() -> None:
    body = _client().get(
        "/api/system-ops", headers={"X-FSO-Use-Fixture": "1"}
    ).json()
    assert body["source"] == "fixture"

    runs = body["recentProtocolRuns"]
    # Deterministic sample history so the evidence chips (Slice 79) are visible
    # in fixture / visual mode without depending on the local audit log.
    assert len(runs) == 3
    assert {run["protocol"] for run in runs} == {
        "calculate_indicators",
        "refresh_market_data",
        "seed_sample_events",
    }
    for run in runs:
        assert run["detailEvidence"]
        assert {"key", "value"}.issubset(run["detailEvidence"][0].keys())
    assert any(
        item["key"] == "snapshots"
        for run in runs
        for item in run["detailEvidence"]
    )


def test_system_ops_protocol_runs_are_audited_to_db(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        post_body = _client().post("/api/system-ops/seed-sample-account").json()
        assert post_body["protocol"] == "seed_sample_account"
        assert post_body["status"] == "OK"

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            rows = SystemOpsProtocolRunRepository(session).list_recent(limit=10)
            assert len(rows) == 1
            assert rows[0].protocol == "seed_sample_account"
            assert rows[0].status == "OK"
            assert rows[0].db_status == "LIVE"

        get_body = _client().get("/api/system-ops").json()
        assert get_body["source"] == "live"
        assert get_body["recentProtocolRuns"][0]["protocol"] == "seed_sample_account"
        protocol = next(
            item
            for item in get_body["protocols"]
            if item["key"] == "seed_sample_account"
        )
        assert protocol["lastRunAt"] == get_body["recentProtocolRuns"][0]["ranAt"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses(
    monkeypatch,
    tmp_path,
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        first = _client().post("/api/system-ops/seed-sample-events").json()
        second = _client().post("/api/system-ops/seed-sample-events").json()

        assert first["protocol"] == "seed_sample_events"
        assert first["status"] == "OK"
        assert "boundary=system_ops" in first["detail"]
        assert "created_count=" in first["detail"]
        assert "CONFIRMED" not in first["detail"]
        assert {"key": "boundary", "value": "system_ops"} in first["detailEvidence"]
        assert any(item["key"] == "created_count" for item in first["detailEvidence"])
        assert second["status"] == "NOOP"
        assert second["detail"] == "noop_existing,boundary=system_ops"
        assert second["detailEvidence"] == [
            {"key": "detail", "value": "noop_existing"},
            {"key": "boundary", "value": "system_ops"},
        ]

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            events = EventRepository(session).list_all()
            assert events
            assert {event.date_status for event in events}.issubset(
                {"TENTATIVE", "SPECULATIVE", "WINDOW"}
            )
            rows = SystemOpsProtocolRunRepository(session).list_recent(limit=10)
            assert [row.protocol for row in rows[:2]] == [
                "seed_sample_events",
                "seed_sample_events",
            ]
        get_body = _client().get("/api/system-ops").json()
        assert get_body["recentProtocolRuns"][0]["detailEvidence"] == [
            {"key": "detail", "value": "noop_existing"},
            {"key": "boundary", "value": "system_ops"},
        ]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_get_exposes_worker_cycle_status(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    with factory() as session:
        WorkerCycleRunRepository(session).create(
            status="OK",
            started_at=now,
            finished_at=now,
            timeframe="1d",
            market_status="OK",
            news_status="NOOP",
            indicator_status="OK",
            market_scope="folder",
            news_scope="folder",
            indicator_scope="folder",
            summary={"startedAt": now.isoformat(), "finishedAt": now.isoformat()},
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/system-ops").json()

        assert body["source"] == "live"
        assert body["workerStatus"]["status"] == "OK"
        assert body["workerStatus"]["latestStartedAt"].startswith("2026-05-27T12:00:00")
        assert "market=OK/folder" in body["workerStatus"]["latestDetail"]
        assert body["workerStatus"]["recentCycles"][0]["indicatorScope"] == "folder"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_get_exposes_worker_cycle_error_detail(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    with factory() as session:
        WorkerCycleRunRepository(session).create(
            status="ERROR",
            started_at=now,
            finished_at=now,
            timeframe="1d",
            market_status="SKIPPED",
            news_status="SKIPPED",
            indicator_status="SKIPPED",
            market_scope="unknown",
            news_scope="unknown",
            indicator_scope="unknown",
            summary={
                "startedAt": now.isoformat(),
                "finishedAt": now.isoformat(),
                "status": "ERROR",
                "error": {"type": "ValueError", "message": "bad adapter"},
            },
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().get("/api/system-ops").json()

        assert body["workerStatus"]["status"] == "ERROR"
        assert "error=ValueError" in body["workerStatus"]["latestDetail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_system_ops_get_exposes_worker_cadence_status(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    now = datetime.now(tz=timezone.utc)
    with factory() as session:
        WorkerCycleRunRepository(session).create(
            status="OK",
            started_at=now - timedelta(seconds=130),
            finished_at=now - timedelta(seconds=120),
            timeframe="1d",
            market_status="OK",
            news_status="NOOP",
            indicator_status="OK",
            market_scope="all_active",
            news_scope="all_active",
            indicator_scope="all_active",
            summary={"startedAt": now.isoformat(), "finishedAt": now.isoformat()},
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_WORKER_INTERVAL_SECONDS", "30")
    monkeypatch.setenv("FINSKILLOS_WORKER_STALE_GRACE_SECONDS", "30")
    reset_settings_cache()

    try:
        body = _client().get("/api/system-ops").json()

        assert body["workerStatus"]["status"] == "OK"
        assert body["workerStatus"]["cadenceStatus"] == "STALE"
        assert body["workerStatus"]["expectedNextCycleAt"]
        assert "Overdue" in body["workerStatus"]["cadenceDetail"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_market_data_protocol_enqueues_worker_job(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-market-data").json()

        # Slice 114: the API enqueues a worker job instead of blocking on the
        # provider; the worker (Slice 113) runs it.
        assert body["protocol"] == "refresh_market_data"
        assert body["status"] == "QUEUED"
        assert "queued for the worker" in body["message"]
        assert "job_queued" in body["detail"]
        assert {"key": "job_type", "value": "refresh_market"} in body["detailEvidence"]
        assert any(item["key"] == "job_id" for item in body["detailEvidence"])

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            jobs = WorkerJobRepository(session).list_recent()
            assert [j.job_type for j in jobs] == ["refresh_market"]
            assert jobs[0].status == "QUEUED"
            assert jobs[0].requested_by == "system_ops"
            # The API does not run the refresh itself — no bars written yet.
            assert MarketRepository(session).count_for("SPY", "1d") == 0
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_seed_sample_account_repairs_snapshot_only_seed_state(
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
        PortfolioRepository(session).create_snapshot(
            account_id=account.id,
            snapshot_date=date(2026, 5, 27),
            total_value=57000000,
            cash_value=7000000,
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/seed-sample-account").json()

        assert body["protocol"] == "seed_sample_account"
        assert body["status"] == "OK"
        assert "positions_created=5" in body["detail"]
        assert {"key": "positions_created", "value": "5"} in body["detailEvidence"]

        with factory() as session:
            positions = PositionRepository(session).list_for_account(account.id)
            assert len(positions) == 5
            assert sum(p.market_value for p in positions) == 50000000
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_market_data_protocol_enqueue_is_idempotent(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        first = _client().post("/api/system-ops/refresh-market-data").json()
        second = _client().post("/api/system-ops/refresh-market-data").json()

        # Repeated clicks while a job is still pending return the same job — the
        # queue never duplicates work.
        assert first["status"] == second["status"] == "QUEUED"

        def _job_id(body: dict) -> str:
            return next(
                item["value"]
                for item in body["detailEvidence"]
                if item["key"] == "job_id"
            )

        assert _job_id(first) == _job_id(second)
        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            assert (
                WorkerJobRepository(session).count_by_status() == {"QUEUED": 1}
            )
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_news_protocol_enqueues_worker_job(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    feed_path = tmp_path / "feed.xml"
    feed_path.write_text(
        """\
<rss version="2.0">
  <channel>
    <title>Market Desk</title>
    <item>
      <title>TSLA delivery numbers top expectations</title>
      <link>https://news.example.com/tsla-deliveries</link>
      <pubDate>Tue, 26 May 2026 12:30:00 GMT</pubDate>
      <description>TSLA delivery update was strong.</description>
    </item>
  </channel>
</rss>
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_NEWS_REFRESH_ADAPTER", "rss")
    monkeypatch.setenv("FINSKILLOS_NEWS_RSS_FEEDS", feed_path.resolve().as_uri())
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-news").json()

        # Slice 114: enqueue, not synchronous ingest — the worker ingests.
        assert body["protocol"] == "refresh_news"
        assert body["status"] == "QUEUED"
        assert {"key": "job_type", "value": "refresh_news"} in body["detailEvidence"]

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            jobs = WorkerJobRepository(session).list_recent()
            assert jobs and jobs[0].job_type == "refresh_news"
            assert NewsArticleRepository(session).latest() == []
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_calculate_indicators_protocol_enqueues_worker_job(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/calculate-indicators").json()

        # Slice 114: enqueue, not synchronous compute — the worker computes
        # (and decides OK / NOOP at process time, e.g. no bars → NOOP).
        assert body["protocol"] == "calculate_indicators"
        assert body["status"] == "QUEUED"
        assert (
            {"key": "job_type", "value": "calculate_indicators"}
            in body["detailEvidence"]
        )

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            jobs = WorkerJobRepository(session).list_recent()
            assert jobs and jobs[0].job_type == "calculate_indicators"
            assert IndicatorRepository(session).latest_for("SPY", "1d") is None
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_events_protocol_ingests_calendar(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        first = _client().post("/api/system-ops/refresh-events").json()
        second = _client().post("/api/system-ops/refresh-events").json()

        assert first["protocol"] == "refresh_events"
        assert first["status"] == "OK"
        assert "events_ingested" in first["detail"]
        assert "created_count=" in first["detail"]
        assert "CONFIRMED" not in first["detail"]
        assert {"key": "boundary", "value": "system_ops"} in first["detailEvidence"]
        # Idempotent — a second run ingests nothing new.
        assert second["status"] == "NOOP"

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            events = EventRepository(session).list_all()
            assert events
            assert {event.date_status for event in events}.issubset(
                {"TENTATIVE", "WINDOW"}
            )
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_events_protocol_uses_csv_adapter(monkeypatch, tmp_path) -> None:
    from pathlib import Path

    csv_path = (
        Path(__file__).parent / "fixtures" / "events" / "calendar_sample.csv"
    )
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_EVENT_CALENDAR_ADAPTER", "csv")
    monkeypatch.setenv("FINSKILLOS_EVENT_CALENDAR_CSV", str(csv_path))
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-events").json()
        assert body["protocol"] == "refresh_events"
        assert body["status"] == "OK"
        assert "events_ingested" in body["detail"]

        factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        with factory() as session:
            titles = {event.title for event in EventRepository(session).list_all()}
            assert "ECB policy decision window" in titles
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_refresh_events_protocol_csv_without_path_is_error(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_EVENT_CALENDAR_ADAPTER", "csv")
    monkeypatch.delenv("FINSKILLOS_EVENT_CALENDAR_CSV", raising=False)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-events").json()
        # Misconfiguration surfaces as a structured ERROR, not a raw 500.
        assert body["status"] == "ERROR"
        assert body["detail"] == "ValueError"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_event_calendar_adapter_selects_http(monkeypatch) -> None:
    """Slice 107 — http branch builds the HttpEventCalendarAdapter from env.

    Construction only; no fetch, so no network is touched."""
    from api.routes.system_ops import _event_calendar_adapter
    from finskillos.data_sources.event_adapter import HttpEventCalendarAdapter

    monkeypatch.setenv("FINSKILLOS_EVENT_CALENDAR_ADAPTER", "http")
    monkeypatch.setenv(
        "FINSKILLOS_EVENT_CALENDAR_URL", "https://vendorx.example/calendar"
    )
    adapter = _event_calendar_adapter()
    assert isinstance(adapter, HttpEventCalendarAdapter)
    assert adapter.url == "https://vendorx.example/calendar"


def test_refresh_events_protocol_http_without_url_is_error(
    monkeypatch, tmp_path
) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("FINSKILLOS_EVENT_CALENDAR_ADAPTER", "http")
    monkeypatch.delenv("FINSKILLOS_EVENT_CALENDAR_URL", raising=False)
    reset_settings_cache()

    try:
        body = _client().post("/api/system-ops/refresh-events").json()
        # Missing URL surfaces as a structured ERROR, not a raw 500 / network call.
        assert body["status"] == "ERROR"
        assert body["detail"] == "ValueError"
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_worker_live_mode_toggle(monkeypatch, tmp_path) -> None:
    """Slice 117 — the cockpit can turn the worker's auto-refresh on/off, and
    System Ops reports the current state."""
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()
    try:
        client = _client()
        # Default ON.
        assert client.get("/api/system-ops").json()["workerStatus"]["liveMode"] is True

        off = client.post(
            "/api/system-ops/worker-live-mode", json={"liveMode": False}
        ).json()
        assert off["liveMode"] is False
        assert "OFF" in off["message"]
        assert client.get("/api/system-ops").json()["workerStatus"]["liveMode"] is False

        on = client.post(
            "/api/system-ops/worker-live-mode", json={"liveMode": True}
        ).json()
        assert on["liveMode"] is True
        assert "ON" in on["message"]
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()
