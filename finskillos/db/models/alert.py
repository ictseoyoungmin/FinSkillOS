"""Risk Firewall alert — output of a guard evaluation.

Alerts are append-only. The `payload` column stores guard-specific context
(thresholds, observed values, affected positions, suggested watchpoints) as
portable JSON. On PostgreSQL the variant resolves to JSONB so GIN indexing
and `->>` lookups stay available; on SQLite (used for migration smoke tests)
it stays plain JSON without the dialect-specific operators.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base

# Portable JSON column type: JSONB on Postgres, JSON elsewhere (e.g. SQLite tests).
JSONPayload = JSON().with_variant(JSONB(), "postgresql")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_date_severity", "alert_date", "severity"),
        Index("idx_alerts_active", "resolved", "severity", "alert_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("accounts.id", ondelete="CASCADE")
    )
    alert_date: Mapped[date] = mapped_column(Date, nullable=False)
    guard_name: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # YELLOW / ORANGE / RED
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONPayload)
    resolved: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account = relationship("Account", back_populates="alerts")
