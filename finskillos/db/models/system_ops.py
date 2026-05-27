"""System Ops protocol audit trail."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base


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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
