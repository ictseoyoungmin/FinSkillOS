"""Symbol subscription model for refresh universe membership."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base


class SymbolSubscription(Base):
    __tablename__ = "symbol_subscriptions"
    __table_args__ = (
        UniqueConstraint("ticker", name="uq_symbol_subscriptions_ticker"),
        Index("idx_symbol_subscriptions_active_ticker", "active", "ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    source: Mapped[str] = mapped_column(
        String(32), default="user", server_default="user", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
