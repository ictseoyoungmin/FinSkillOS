"""Cached ticker logo metadata."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base


class SymbolLogoCache(Base):
    __tablename__ = "symbol_logo_cache"
    __table_args__ = (
        UniqueConstraint("ticker", name="uq_symbol_logo_cache_ticker"),
        Index("idx_symbol_logo_cache_provider", "provider", "ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(24), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    logo_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
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
