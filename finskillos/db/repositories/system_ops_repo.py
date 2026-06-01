"""Repositories for System Ops and worker audit records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finskillos.db.models import (
    SystemOpsProtocolRun,
    WorkerControl,
    WorkerCycleRun,
    WorkerJob,
)
from finskillos.db.models.system_ops import (
    JOB_STATUS_ACTIVE,
    JOB_STATUS_DONE,
    JOB_STATUS_ERROR,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    WORKER_CONTROL_SINGLETON_ID,
    _utcnow,
)


class SystemOpsProtocolRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        protocol: str,
        status: str,
        message: str,
        detail: str,
        db_status: str,
        source: str,
        ran_at: datetime,
    ) -> SystemOpsProtocolRun:
        row = SystemOpsProtocolRun(
            protocol=protocol,
            status=status,
            message=message,
            detail=detail,
            db_status=db_status,
            source=source,
            ran_at=ran_at,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_recent(self, limit: int = 5) -> list[SystemOpsProtocolRun]:
        stmt = (
            select(SystemOpsProtocolRun)
            .order_by(SystemOpsProtocolRun.ran_at.desc(), SystemOpsProtocolRun.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def latest_by_protocol(self) -> dict[str, SystemOpsProtocolRun]:
        rows = list(
            self.session.scalars(
                select(SystemOpsProtocolRun).order_by(
                    SystemOpsProtocolRun.ran_at.desc(),
                    SystemOpsProtocolRun.created_at.desc(),
                )
            )
        )
        latest: dict[str, SystemOpsProtocolRun] = {}
        for row in rows:
            latest.setdefault(row.protocol, row)
        return latest


class WorkerCycleRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        status: str,
        started_at: datetime,
        finished_at: datetime,
        timeframe: str,
        market_status: str,
        news_status: str,
        indicator_status: str,
        market_scope: str,
        news_scope: str,
        indicator_scope: str,
        summary: dict,
    ) -> WorkerCycleRun:
        row = WorkerCycleRun(
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            timeframe=timeframe,
            market_status=market_status,
            news_status=news_status,
            indicator_status=indicator_status,
            market_scope=market_scope,
            news_scope=news_scope,
            indicator_scope=indicator_scope,
            summary=summary,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def list_recent(self, limit: int = 5) -> list[WorkerCycleRun]:
        stmt = (
            select(WorkerCycleRun)
            .order_by(WorkerCycleRun.started_at.desc(), WorkerCycleRun.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def latest(self) -> WorkerCycleRun | None:
        stmt = (
            select(WorkerCycleRun)
            .order_by(WorkerCycleRun.started_at.desc(), WorkerCycleRun.created_at.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()


class WorkerJobRepository:
    """Postgres-backed worker job queue (Slice 113).

    ``enqueue`` is idempotent while a job is still active so a request never
    queues duplicate work; ``claim_next`` atomically claims the oldest queued
    job (``FOR UPDATE SKIP LOCKED`` on postgres) so concurrent workers cannot
    double-process one.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def enqueue(
        self,
        job_type: str,
        *,
        payload: dict | None = None,
        requested_by: str = "system",
        dedup_key: str | None = None,
    ) -> WorkerJob:
        existing = self._active(job_type, dedup_key)
        if existing is not None:
            return existing
        row = WorkerJob(
            job_type=job_type,
            status=JOB_STATUS_QUEUED,
            payload=payload,
            requested_by=requested_by,
            dedup_key=dedup_key,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def _active(self, job_type: str, dedup_key: str | None) -> WorkerJob | None:
        stmt = select(WorkerJob).where(
            WorkerJob.job_type == job_type,
            WorkerJob.status.in_(JOB_STATUS_ACTIVE),
        )
        if dedup_key is None:
            stmt = stmt.where(WorkerJob.dedup_key.is_(None))
        else:
            stmt = stmt.where(WorkerJob.dedup_key == dedup_key)
        return self.session.scalars(stmt.limit(1)).first()

    def claim_next(self) -> WorkerJob | None:
        stmt = (
            select(WorkerJob)
            .where(WorkerJob.status == JOB_STATUS_QUEUED)
            .order_by(WorkerJob.created_at)
            .limit(1)
        )
        if self.session.get_bind().dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)
        job = self.session.scalars(stmt).first()
        if job is None:
            return None
        job.status = JOB_STATUS_RUNNING
        job.started_at = _utcnow()
        self.session.flush()
        return job

    def complete(self, job: WorkerJob, result: dict | None = None) -> WorkerJob:
        job.status = JOB_STATUS_DONE
        job.result = result
        job.finished_at = _utcnow()
        self.session.flush()
        return job

    def fail(self, job: WorkerJob, error: str) -> WorkerJob:
        job.status = JOB_STATUS_ERROR
        job.error = error
        job.finished_at = _utcnow()
        self.session.flush()
        return job

    def get(self, job_id) -> WorkerJob | None:
        return self.session.get(WorkerJob, job_id)

    def list_recent(self, limit: int = 20) -> list[WorkerJob]:
        stmt = (
            select(WorkerJob)
            .order_by(WorkerJob.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def count_by_status(self) -> dict[str, int]:
        stmt = select(WorkerJob.status, func.count()).group_by(WorkerJob.status)
        return {status: count for status, count in self.session.execute(stmt)}


class WorkerControlRepository:
    """Single-row worker runtime control (Slice 117 — live-mode toggle)."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> WorkerControl:
        row = self.session.get(WorkerControl, WORKER_CONTROL_SINGLETON_ID)
        if row is None:
            row = WorkerControl(id=WORKER_CONTROL_SINGLETON_ID, live_mode=True)
            self.session.add(row)
            self.session.flush()
        return row

    def is_live_mode(self) -> bool:
        return bool(self.get().live_mode)

    def set_live_mode(self, enabled: bool, *, updated_by: str = "system") -> WorkerControl:
        row = self.get()
        row.live_mode = bool(enabled)
        row.updated_at = _utcnow()
        row.updated_by = updated_by
        self.session.flush()
        return row
