from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from finskillos.db.base import Base


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (UniqueConstraint("account_id", "snapshot_date", name="uq_portfolio_snapshot_account_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cash_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="snapshots")
    positions = relationship("PortfolioPosition", back_populates="snapshot", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("portfolio_snapshots.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(160))
    asset_class: Mapped[str] = mapped_column(String(40), default="equity", server_default="equity")
    sector: Mapped[str | None] = mapped_column(String(80))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    snapshot = relationship("PortfolioSnapshot", back_populates="positions")
