"""System Ops and worker audit trails."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, DateTime, Index, String, Text, Uuid, func
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
    market_scope: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    news_scope: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    indicator_scope: Mapped[str] = mapped_column(
        String(32), default="unknown", nullable=False
    )
    summary: Mapped[dict | None] = mapped_column(JSONPayload)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
