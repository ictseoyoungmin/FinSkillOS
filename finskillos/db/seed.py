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
from finskillos.db.repositories import (
    AccountRepository,
    PortfolioRepository,
    PositionRepository,
)

DEFAULT_INITIAL_TOTAL_VALUE = Decimal("57000000")
DEFAULT_INITIAL_CASH_VALUE = Decimal("7000000")
DEFAULT_SAMPLE_POSITION_WEIGHTS = (
    ("NVDA", "Semiconductors", "AI Infrastructure", Decimal("0.30")),
    ("TSLA", "Consumer Discretionary", "EV / Robotaxi", Decimal("0.24")),
    ("AAPL", "Technology", "Mega Cap Tech", Decimal("0.20")),
    ("MSFT", "Technology", "Cloud / AI", Decimal("0.16")),
    ("RKLB", "Aerospace", "Space / Launch", Decimal("0.10")),
)
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class SeedResult:
    account: Account
    initial_snapshot: PortfolioSnapshot | None
    created_account: bool
    created_snapshot: bool
    created_positions: int = 0


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
    positions = PositionRepository(session)

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

    created_positions = _ensure_sample_positions(
        positions=positions,
        account_id=account.id,
        snapshot=snapshot,
        created_account=created_account,
        created_snapshot=created_snapshot,
    )

    return SeedResult(
        account=account,
        initial_snapshot=snapshot,
        created_account=created_account,
        created_snapshot=created_snapshot,
        created_positions=created_positions,
    )


def _ensure_sample_positions(
    *,
    positions: PositionRepository,
    account_id,
    snapshot: PortfolioSnapshot | None,
    created_account: bool,
    created_snapshot: bool,
) -> int:
    """Create sample positions only for the seed-owned baseline state."""

    if snapshot is None:
        return 0
    if positions.list_for_account(account_id):
        return 0
    if not (
        created_account
        or created_snapshot
        or _looks_like_original_seed_snapshot(snapshot)
    ):
        return 0

    investable_value = Decimal(snapshot.total_value) - Decimal(snapshot.cash_value)
    if investable_value <= 0:
        return 0

    created = 0
    allocated = Decimal("0")
    last_index = len(DEFAULT_SAMPLE_POSITION_WEIGHTS) - 1
    for index, (ticker, sector, theme, weight) in enumerate(
        DEFAULT_SAMPLE_POSITION_WEIGHTS
    ):
        if index == last_index:
            market_value = investable_value - allocated
        else:
            market_value = (investable_value * weight).quantize(_CENT)
            allocated += market_value
        positions.create(
            account_id=account_id,
            ticker=ticker,
            quantity=Decimal("1"),
            market_value=market_value,
            sector=sector,
            theme=theme,
            strategy_type="sample",
            thesis="Seeded sample position for portfolio-context demos.",
        )
        created += 1
    return created


def _looks_like_original_seed_snapshot(snapshot: PortfolioSnapshot) -> bool:
    return (
        Decimal(snapshot.total_value) == DEFAULT_INITIAL_TOTAL_VALUE
        and Decimal(snapshot.cash_value) == DEFAULT_INITIAL_CASH_VALUE
    )
