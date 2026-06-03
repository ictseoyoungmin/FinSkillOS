"""System Ops and worker audit trails."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base

JSONPayload = JSON().with_variant(JSONB(), "postgresql")

_utcnow_lock = threading.Lock()
_utcnow_last: datetime | None = None


def _utcnow() -> datetime:
    """Strictly-monotonic, microsecond-precision insert time.

    Used as the ORM-side ``created_at`` default so two audit rows written in the
    same process (``ran_at`` / ``started_at`` are stored only at second
    precision) order deterministically by insertion time in ``list_recent``.
    Microsecond wall-clock alone can still tie on a fast host, so each call
    returns a value strictly greater than the previous one.
    """
    global _utcnow_last
    with _utcnow_lock:
        now = datetime.now(timezone.utc)
        if _utcnow_last is not None and now <= _utcnow_last:
            now = _utcnow_last + timedelta(microseconds=1)
        _utcnow_last = now
        return now


class SystemOpsProtocolRun(Base):
    __tablename__ = "system_ops_protocol_runs"
    __table_args__ = (
        Index("idx_system_ops_protocol_runs_protocol_time", "protocol", "ran_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    protocol: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    db_status: Mapped[str] = mapped_column(
        String(16), default="UNKNOWN", server_default="UNKNOWN", nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(16), default="live", server_default="live", nullable=False
    )
    ran_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )


class WorkerCycleRun(Base):
    __tablename__ = "worker_cycle_runs"
    __table_args__ = (
        Index("idx_worker_cycle_runs_started_at", "started_at"),
        Index("idx_worker_cycle_runs_status_time", "status", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(16), default="1d", nullable=False)
    market_status: Mapped[str] = mapped_column(String(16), default="SKIPPED", nullable=False)
    news_status: Mapped[str] = mapped_column(String(16), default="SKIPPED", nullable=False)
    indicator_status: Mapped[str] = mapped_column(
        String(16), default="SKIPPED", nullable=False
    )
    # 80 chars holds folder-scoped audit labels like
    # "collection:indicator:folder=<uuid>" (Slice 134 / F3).
    market_scope: Mapped[str] = mapped_column(String(80), default="unknown", nullable=False)
    news_scope: Mapped[str] = mapped_column(String(80), default="unknown", nullable=False)
    indicator_scope: Mapped[str] = mapped_column(
        String(80), default="unknown", nullable=False
    )
    summary: Mapped[dict | None] = mapped_column(JSONPayload)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )


# Worker job queue (Slice 113) ------------------------------------------------

JOB_STATUS_QUEUED = "QUEUED"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_DONE = "DONE"
JOB_STATUS_ERROR = "ERROR"
JOB_STATUS_ACTIVE = (JOB_STATUS_QUEUED, JOB_STATUS_RUNNING)

WORKER_JOB_REFRESH_ALL = "refresh_all"
WORKER_JOB_REFRESH_MARKET = "refresh_market"
WORKER_JOB_REFRESH_NEWS = "refresh_news"
WORKER_JOB_CALCULATE_INDICATORS = "calculate_indicators"
WORKER_JOB_TYPES = (
    WORKER_JOB_REFRESH_ALL,
    WORKER_JOB_REFRESH_MARKET,
    WORKER_JOB_REFRESH_NEWS,
    WORKER_JOB_CALCULATE_INDICATORS,
)


class WorkerJob(Base):
    """A queued refresh request the worker claims and processes.

    The worker idles, then claims the oldest ``QUEUED`` job (postgres
    ``FOR UPDATE SKIP LOCKED`` so concurrent workers never double-claim),
    runs the matching refresh, and records the outcome. ``enqueue`` is
    idempotent on ``(job_type, dedup_key)`` while a job is still active, so a
    request never piles up duplicate work.
    """

    __tablename__ = "worker_jobs"
    __table_args__ = (
        Index("idx_worker_jobs_status_created", "status", "created_at"),
        Index("idx_worker_jobs_type_dedup_status", "job_type", "dedup_key", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=JOB_STATUS_QUEUED, nullable=False
    )
    dedup_key: Mapped[str | None] = mapped_column(String(128))
    requested_by: Mapped[str] = mapped_column(
        String(32), default="system", nullable=False
    )
    payload: Mapped[dict | None] = mapped_column(JSONPayload)
    result: Mapped[dict | None] = mapped_column(JSONPayload)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Worker control (Slice 117) --------------------------------------------------

WORKER_CONTROL_SINGLETON_ID = 1


class WorkerControl(Base):
    """Single-row runtime control for the worker's automatic live refresh.

    ``live_mode`` gates the worker's auto-enqueue (on start + interval). When
    off, the worker idles and only processes explicitly-requested jobs (System
    Ops refresh buttons still work). Toggled from the cockpit; read by the
    worker each cycle so the change takes effect without a restart.
    """

    __tablename__ = "worker_control"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, default=WORKER_CONTROL_SINGLETON_ID
    )
    live_mode: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=func.true(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_by: Mapped[str] = mapped_column(
        String(32), default="system", nullable=False
    )


class SystemOpsSettings(Base):
    """Persisted override settings for runtime operations and refresh workers.

    This single-row JSON document contains only values that should override
    `.env` defaults at startup. Missing keys keep `.env` semantics. The UI reads
    and edits this table via the System Ops settings endpoints.
    """

    __tablename__ = "system_ops_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1,
    )
    values: Mapped[dict] = mapped_column(
        JSONPayload,
        default=dict,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_by: Mapped[str] = mapped_column(
        String(32),
        default="system",
        nullable=False,
    )


class SystemOpsSettingsHistory(Base):
    """One row per runtime-setting key change (Slice 149).

    The overlay itself is a single document carrying only the latest values; this
    table is the append-only change log: who changed which key from what to what,
    and when. ``new_value=None`` means the key was reverted to its ``.env`` default.
    """

    __tablename__ = "system_ops_settings_history"
    __table_args__ = (
        Index("idx_system_ops_settings_history_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    setting_key: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(512))
    new_value: Mapped[str | None] = mapped_column(String(512))
    updated_by: Mapped[str] = mapped_column(String(32), default="system", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
