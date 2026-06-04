"""Slice 113 — Postgres worker job queue + worker consumption."""

from __future__ import annotations

import dataclasses
from contextlib import contextmanager

from sqlalchemy.orm import Session

import scripts.refresh_worker as rw
from finskillos.db.models.system_ops import (
    JOB_STATUS_DONE,
    JOB_STATUS_QUEUED,
    WORKER_JOB_REFRESH_ALL,
    WORKER_JOB_REFRESH_MARKET,
)
from finskillos.db.repositories import MarketRepository, WorkerJobRepository


def test_enqueue_is_idempotent_while_active(db_session: Session) -> None:
    repo = WorkerJobRepository(db_session)
    first = repo.enqueue(WORKER_JOB_REFRESH_ALL, dedup_key=WORKER_JOB_REFRESH_ALL)
    second = repo.enqueue(WORKER_JOB_REFRESH_ALL, dedup_key=WORKER_JOB_REFRESH_ALL)
    db_session.flush()
    assert first.id == second.id  # no duplicate queued job
    assert repo.count_by_status() == {JOB_STATUS_QUEUED: 1}

    # Once the active job finishes, a new request enqueues a fresh one.
    repo.complete(first, {"ok": True})
    third = repo.enqueue(WORKER_JOB_REFRESH_ALL, dedup_key=WORKER_JOB_REFRESH_ALL)
    assert third.id != first.id
    assert repo.count_by_status() == {JOB_STATUS_DONE: 1, JOB_STATUS_QUEUED: 1}


def test_claim_next_is_fifo_and_marks_running(db_session: Session) -> None:
    repo = WorkerJobRepository(db_session)
    a = repo.enqueue(WORKER_JOB_REFRESH_MARKET, dedup_key="a")
    b = repo.enqueue(WORKER_JOB_REFRESH_MARKET, dedup_key="b")
    db_session.flush()

    claimed = repo.claim_next()
    assert claimed.id == a.id  # oldest first
    assert claimed.status == "RUNNING"
    assert claimed.started_at is not None
    # The next claim returns the second job, never the already-RUNNING one.
    assert repo.claim_next().id == b.id
    assert repo.claim_next() is None


def test_reap_stale_running_marks_old_claims_error(db_session: Session) -> None:
    # Slice 156: a job stuck RUNNING (worker died mid-claim) past the grace is
    # reaped to ERROR (and so becomes retryable); a fresh claim is left alone.
    from datetime import datetime, timedelta, timezone

    repo = WorkerJobRepository(db_session)
    repo.enqueue(WORKER_JOB_REFRESH_ALL, dedup_key="stale")
    repo.enqueue(WORKER_JOB_REFRESH_MARKET, dedup_key="fresh")
    db_session.flush()
    stale = repo.claim_next()  # oldest → stale
    fresh = repo.claim_next()  # → fresh
    assert stale.status == "RUNNING" and fresh.status == "RUNNING"
    # Backdate the stale job's started_at well past the grace.
    stale.started_at = datetime.now(tz=timezone.utc) - timedelta(hours=2)
    db_session.flush()

    cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=30)
    reaped = repo.reap_stale_running(older_than=cutoff)

    assert reaped == 1
    assert repo.get(stale.id).status == "ERROR"
    assert "reaped" in repo.get(stale.id).error
    assert repo.get(fresh.id).status == "RUNNING"  # still genuinely running


def test_fail_records_error(db_session: Session) -> None:
    repo = WorkerJobRepository(db_session)
    job = repo.enqueue(WORKER_JOB_REFRESH_ALL)
    repo.fail(repo.claim_next(), "BoomError: provider down")
    assert job.status == "ERROR"
    assert "BoomError" in job.error
    assert job.finished_at is not None


def _patch_scope(monkeypatch, session: Session) -> None:
    @contextmanager
    def _scope():
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    monkeypatch.setattr(rw, "session_scope", _scope)


def test_drain_queue_processes_market_job(db_session: Session, monkeypatch) -> None:
    WorkerJobRepository(db_session).enqueue(
        WORKER_JOB_REFRESH_MARKET,
        dedup_key=WORKER_JOB_REFRESH_MARKET,
        requested_by="test",
    )
    db_session.commit()
    _patch_scope(monkeypatch, db_session)

    args = rw.build_parser().parse_args(["--once"])
    config = dataclasses.replace(
        rw.load_config(args),
        market_adapter="mock",
        market_tickers=("SPY",),
        indicator_tickers=("SPY",),
        timeframe="1d",
    )

    processed = rw.drain_queue(config)
    assert processed == 1

    job = WorkerJobRepository(db_session).list_recent()[0]
    assert job.status == JOB_STATUS_DONE
    assert job.result["market"]["status"] in {"OK", "NOOP"}
    # The market refresh actually wrote SPY bars via the mock adapter.
    assert MarketRepository(db_session).list_bars("SPY", "1d")


def test_drain_queue_applies_runtime_overrides_from_job_payload(
    db_session: Session, monkeypatch
) -> None:
    job_payload = {
        "runtime_settings": {
            "FINSKILLOS_MARKET_REFRESH_TICKERS": "AAPL",
            "FINSKILLOS_MARKET_REFRESH_TIMEFRAME": "1d",
        }
    }
    WorkerJobRepository(db_session).enqueue(
        WORKER_JOB_REFRESH_MARKET,
        dedup_key="override",
        requested_by="test",
        payload=job_payload,
    )
    db_session.commit()
    _patch_scope(monkeypatch, db_session)

    args = rw.build_parser().parse_args(["--once"])
    config = dataclasses.replace(
        rw.load_config(args),
        market_adapter="mock",
        market_tickers=("SPY",),
        indicator_tickers=("SPY",),
        timeframe="1d",
    )

    processed = rw.drain_queue(config)
    assert processed == 1

    assert MarketRepository(db_session).count_for("AAPL", "1d") > 0
    assert MarketRepository(db_session).count_for("SPY", "1d") == 0


def test_drain_queue_marks_unknown_job_error(db_session: Session, monkeypatch) -> None:
    WorkerJobRepository(db_session).enqueue("bogus_job", dedup_key="bogus")
    db_session.commit()
    _patch_scope(monkeypatch, db_session)

    args = rw.build_parser().parse_args(["--once"])
    processed = rw.drain_queue(rw.load_config(args))
    assert processed == 1
    job = WorkerJobRepository(db_session).list_recent()[0]
    assert job.status == "ERROR"
    assert "unknown worker job type" in job.error


# Slice 117 — worker live-mode control -----------------------------------------


def test_worker_control_singleton_and_set(db_session: Session) -> None:
    from finskillos.db.repositories import WorkerControlRepository

    repo = WorkerControlRepository(db_session)
    assert repo.is_live_mode() is True  # default ON
    row = repo.set_live_mode(False, updated_by="test")
    assert row.updated_by == "test"
    assert WorkerControlRepository(db_session).is_live_mode() is False
    # Singleton: a second repo sees the same row.
    assert WorkerControlRepository(db_session).get().id == repo.get().id


def test_live_mode_enabled_reads_control(db_session: Session, monkeypatch) -> None:
    from finskillos.db.repositories import WorkerControlRepository

    _patch_scope(monkeypatch, db_session)
    WorkerControlRepository(db_session).set_live_mode(False)
    db_session.commit()
    assert rw.live_mode_enabled() is False
    WorkerControlRepository(db_session).set_live_mode(True)
    db_session.commit()
    assert rw.live_mode_enabled() is True
