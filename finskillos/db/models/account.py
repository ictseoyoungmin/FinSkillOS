"""Account model — the user's trading account / goal unit."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(
        String(8), default="KRW", server_default="KRW", nullable=False
    )
    target_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    snapshots = relationship(
        "PortfolioSnapshot", back_populates="account", cascade="all, delete-orphan"
    )
    positions = relationship(
        "Position", back_populates="account", cascade="all, delete-orphan"
    )
    trades = relationship(
        "Trade", back_populates="account", cascade="all, delete-orphan"
    )
    alerts = relationship(
        "Alert", back_populates="account", cascade="all, delete-orphan"
    )
