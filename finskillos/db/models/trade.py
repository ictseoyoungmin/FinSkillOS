"""Trade journal entry — one row per executed trade or reflection note.

Trades are the source of Trade Memory and the regime-bucketed reflection
reports. The fields here intentionally capture *why* the trade happened
(reason, thesis, catalyst, emotion_state, market_regime) so post-hoc
analysis can group P&L by regime / sector / mistake tag without
hand-tagging later.

Slice 12 extends the original Slice 02 row with reflection columns:

* ``thesis`` — longer-form reasoning behind the entry.
* ``result_pnl`` / ``result_pnl_pct`` / ``r_multiple`` — descriptive
  outcome captured by the user after the trade closes.
* ``mistake_tags`` — JSON list of normalized tag strings (e.g.
  ``["Chasing", "Oversized"]``). The legacy single-string
  ``mistake_tag`` column is retained for backward compatibility.
* ``notes`` — free-form post-trade reflection.
* ``sector`` / ``theme`` / ``event_key`` — dimension hooks shared with
  the Slice 10/11 News / Event Radar pipelines.
* ``updated_at`` — last edit timestamp so reflection views can show
  the freshest entry without re-querying ``created_at``.

The Slice 12 ``side`` vocabulary is wider (LONG / SHORT / WATCH /
EXIT_REVIEW / OTHER) so journal entries can be saved without an
executed order; ``side`` is widened to 16 chars to accommodate them.
The legacy BUY / SELL values continue to load through the schema.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base

# Cross-dialect JSON column: JSONB on Postgres, JSON elsewhere (SQLite tests).
JSONPayload = JSON().with_variant(JSONB(), "postgresql")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("idx_trades_account_date", "account_id", "trade_date"),
        Index("idx_trades_ticker_date", "ticker", "trade_date"),
        Index("idx_trades_market_regime", "market_regime"),
        Index("idx_trades_strategy_type", "strategy_type"),
        Index("idx_trades_sector", "sector"),
        Index("idx_trades_theme", "theme"),
        Index("idx_trades_event_key", "event_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    strategy_type: Mapped[str] = mapped_column(
        String(80), default="swing", server_default="swing", nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    fees: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    reason: Mapped[str | None] = mapped_column(Text)
    thesis: Mapped[str | None] = mapped_column(Text)
    catalyst: Mapped[str | None] = mapped_column(String(160))
    emotion_state: Mapped[str | None] = mapped_column(String(80))
    market_regime: Mapped[str | None] = mapped_column(String(80))
    mistake_tag: Mapped[str | None] = mapped_column(String(40))
    mistake_tags: Mapped[list | None] = mapped_column(JSONPayload)
    result_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    result_pnl_pct: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    r_multiple: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    notes: Mapped[str | None] = mapped_column(Text)
    sector: Mapped[str | None] = mapped_column(String(80))
    theme: Mapped[str | None] = mapped_column(String(80))
    event_key: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    account = relationship("Account", back_populates="trades")
