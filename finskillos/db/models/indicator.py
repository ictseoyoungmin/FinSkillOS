"""IndicatorSnapshot model — computed technical indicators.

One row per `(ticker, timeframe, snapshot_time)`. Values stay nullable
so a snapshot can be persisted even when there is not enough history
to evaluate a longer-window indicator (e.g. EMA120 needs 120 bars).
`trend_state` is descriptive only — bullish / neutral / bearish — and
never expresses a buy/sell directive.
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


class IndicatorSnapshot(Base):
    __tablename__ = "indicator_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "timeframe",
            "snapshot_time",
            name="uq_indicator_snapshots_ticker_tf_time",
        ),
        Index(
            "idx_indicators_lookup",
            "ticker",
            "timeframe",
            "snapshot_time",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(8), nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    rsi_14: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    ema_20: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ema_60: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ema_120: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    bb_mid: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    bb_upper: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    bb_lower: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    volume_zscore: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    momentum_score: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    trend_state: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="internal")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
