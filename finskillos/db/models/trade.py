"""Trade journal entry — one row per executed buy or sell.

Trades are the source of Trade Memory and the regime-bucketed reflection
reports. The fields here intentionally capture *why* the trade happened
(reason, catalyst, emotion_state, market_regime) so post-hoc analysis can
group P&L by regime / sector / mistake tag without hand-tagging later.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trades_account_date", "account_id", "trade_date"),
        Index("idx_trades_ticker_date", "ticker", "trade_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)  # BUY / SELL
    strategy_type: Mapped[str] = mapped_column(
        String(32), default="swing", server_default="swing", nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    reason: Mapped[str | None] = mapped_column(Text)
    catalyst: Mapped[str | None] = mapped_column(String(160))
    emotion_state: Mapped[str | None] = mapped_column(String(40))
    market_regime: Mapped[str | None] = mapped_column(String(40))
    mistake_tag: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account = relationship("Account", back_populates="trades")
