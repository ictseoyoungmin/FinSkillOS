"""Portfolio snapshot model.

A `PortfolioSnapshot` is the per-day record of total account value, used by
the Mission Control progress tracker and the drawdown guard. Live, current
holdings live in the separate `Position` model so the snapshot history can
stay append-only.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "snapshot_date",
            name="uq_portfolio_snapshot_account_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), server_default="0", nullable=False
    )
    peak_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    account = relationship("Account", back_populates="snapshots")
