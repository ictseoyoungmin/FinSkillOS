"""Default-state seed helpers for the slice-02 DB foundation.

`seed_default_account` is idempotent — if an account with the configured
name already exists it is reused and the initial 57,000,000 KRW snapshot is
only inserted when there is no prior snapshot. Safe to call on every
container boot.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.config import get_settings
from finskillos.db.models import Account, PortfolioSnapshot
from finskillos.db.repositories import AccountRepository, PortfolioRepository

DEFAULT_INITIAL_TOTAL_VALUE = Decimal("57000000")
DEFAULT_INITIAL_CASH_VALUE = Decimal("7000000")


@dataclass(frozen=True)
class SeedResult:
    account: Account
    initial_snapshot: PortfolioSnapshot | None
    created_account: bool
    created_snapshot: bool


def seed_default_account(
    session: Session,
    *,
    snapshot_date: date | None = None,
    initial_total_value: Decimal = DEFAULT_INITIAL_TOTAL_VALUE,
    initial_cash_value: Decimal = DEFAULT_INITIAL_CASH_VALUE,
) -> SeedResult:
    """Ensure the default Main Trading Account + initial snapshot exist."""
    settings = get_settings()

    accounts = AccountRepository(session)
    portfolios = PortfolioRepository(session)

    account = accounts.get_by_name(settings.default_account_name)
    created_account = False
    if account is None:
        account = accounts.create(
            name=settings.default_account_name,
            target_value=settings.target_value,
            base_currency=settings.base_currency,
        )
        created_account = True

    existing_snapshot = portfolios.latest(account.id)
    created_snapshot = False
    snapshot = existing_snapshot
    if existing_snapshot is None:
        snapshot = portfolios.create_snapshot(
            account_id=account.id,
            snapshot_date=snapshot_date or date.today(),
            total_value=initial_total_value,
            cash_value=initial_cash_value,
            peak_value=initial_total_value,
            drawdown_pct=Decimal("0"),
        )
        created_snapshot = True

    return SeedResult(
        account=account,
        initial_snapshot=snapshot,
        created_account=created_account,
        created_snapshot=created_snapshot,
    )
