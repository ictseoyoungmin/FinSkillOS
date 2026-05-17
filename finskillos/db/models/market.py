"""MarketBar model — timeframe-aware OHLCV row.

Stores raw price + volume bars per `(ticker, timeframe, bar_time)`. The
unique constraint matches docs/v2_1/03 §market_bars and protects against
duplicate inserts on re-import. The `source` column records which adapter
(yfinance, csv, mock, ...) produced the row so the Market Kernel can
later surface provenance in Data Health.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from finskillos.db.base import Base


class MarketBar(Base):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "timeframe",
            "bar_time",
            name="uq_market_bars_ticker_tf_time",
        ),
        Index(
            "idx_market_bars_lookup",
            "ticker",
            "timeframe",
            "bar_time",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    bar_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    high: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    low: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    adj_close: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volume: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
