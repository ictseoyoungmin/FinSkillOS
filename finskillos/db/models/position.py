"""Live position model — current holdings with thesis and strategy bucket."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base


class Position(Base):
    """Current open holding for an account.

    Unlike `PortfolioSnapshot`, this is a live, mutable view — the Risk
    Firewall reads `market_value`, `sector`, and `strategy_type` straight off
    this table to compute single-name and sector concentration guards.
    """

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("account_id", "ticker", name="uq_positions_account_ticker"),
        Index("idx_positions_account_ticker", "account_id", "ticker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(80))
    theme: Mapped[str | None] = mapped_column(String(80))
    strategy_type: Mapped[str] = mapped_column(
        String(32), default="swing", server_default="swing", nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    average_cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    pnl_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    thesis: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    account = relationship("Account", back_populates="positions")
