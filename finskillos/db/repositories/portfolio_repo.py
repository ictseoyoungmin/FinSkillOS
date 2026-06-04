"""PortfolioRepository — account-scoped snapshot history."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import PortfolioSnapshot


class PortfolioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_snapshot(
        self,
        *,
        account_id: uuid.UUID,
        snapshot_date: date,
        total_value: Decimal,
        cash_value: Decimal = Decimal("0"),
        peak_value: Decimal | None = None,
        drawdown_pct: Decimal | None = None,
    ) -> PortfolioSnapshot:
        snapshot = PortfolioSnapshot(
            account_id=account_id,
            snapshot_date=snapshot_date,
            total_value=total_value,
            cash_value=cash_value,
            peak_value=peak_value,
            drawdown_pct=drawdown_pct,
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def upsert_snapshot(
        self,
        *,
        account_id: uuid.UUID,
        snapshot_date: date,
        total_value: Decimal,
        cash_value: Decimal = Decimal("0"),
        peak_value: Decimal | None = None,
        drawdown_pct: Decimal | None = None,
    ) -> PortfolioSnapshot:
        existing = self.get_by_account_and_date(account_id, snapshot_date)
        if existing is None:
            return self.create_snapshot(
                account_id=account_id,
                snapshot_date=snapshot_date,
                total_value=total_value,
                cash_value=cash_value,
                peak_value=peak_value,
                drawdown_pct=drawdown_pct,
            )

        existing.total_value = total_value
        existing.cash_value = cash_value
        existing.peak_value = peak_value
        existing.drawdown_pct = drawdown_pct
        self.session.flush()
        return existing

    def get(self, snapshot_id: uuid.UUID) -> PortfolioSnapshot | None:
        return self.session.get(PortfolioSnapshot, snapshot_id)

    def get_by_account_and_date(
        self, account_id: uuid.UUID, snapshot_date: date
    ) -> PortfolioSnapshot | None:
        stmt = select(PortfolioSnapshot).where(
            PortfolioSnapshot.account_id == account_id,
            PortfolioSnapshot.snapshot_date == snapshot_date,
        )
        return self.session.scalars(stmt).one_or_none()

    def update_latest_baseline(
        self,
        account_id: uuid.UUID,
        *,
        snapshot_date: date,
        total_value: Decimal | None = None,
        cash_value: Decimal | None = None,
    ) -> PortfolioSnapshot:
        """Partial-update the latest snapshot's baseline (Slice 158).

        Creates today's snapshot if none exists. ``None`` leaves a field as-is."""
        snapshot = self.latest(account_id)
        if snapshot is None:
            return self.create_snapshot(
                account_id=account_id,
                snapshot_date=snapshot_date,
                total_value=total_value or Decimal("0"),
                cash_value=cash_value or Decimal("0"),
            )
        if total_value is not None:
            snapshot.total_value = total_value
        if cash_value is not None:
            snapshot.cash_value = cash_value
        self.session.flush()
        return snapshot

    def latest(self, account_id: uuid.UUID) -> PortfolioSnapshot | None:
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.account_id == account_id)
            .order_by(PortfolioSnapshot.snapshot_date.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()

    def list_for_account(self, account_id: uuid.UUID) -> list[PortfolioSnapshot]:
        stmt = (
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.account_id == account_id)
            .order_by(PortfolioSnapshot.snapshot_date)
        )
        return list(self.session.scalars(stmt))
