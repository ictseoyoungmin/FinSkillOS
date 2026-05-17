"""Slice 03 — PORT-AC-001 portfolio CSV import flow.

End-to-end: parse the v2.1 sample CSV → write positions and a
portfolio_snapshot via `PortfolioService.import_snapshot` → confirm the
row counts, the snapshot total, and the single-position 1천만원 flag
fire correctly via the read model.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    AccountRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.services.portfolio_service import (
    PortfolioService,
    load_portfolio_csv,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "portfolio"


@pytest.fixture
def account_id(db_session: Session):
    return AccountRepository(db_session).create(
        name="Import Test Account",
        target_value=Decimal("100000000"),
    ).id


def test_import_snapshot_creates_positions_and_snapshot_from_csv(
    db_session: Session, account_id
) -> None:
    rows = load_portfolio_csv(FIXTURES / "sample_portfolio_snapshot.csv")
    service = PortfolioService(db_session)

    snapshot = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("2000000"),
    )

    positions = PositionRepository(db_session).list_for_account(account_id)
    assert {p.ticker for p in positions} == {"TSLA", "NVDA", "RKLB", "PLTR"}

    snapshots = PortfolioRepository(db_session).list_for_account(account_id)
    assert len(snapshots) == 1
    assert snapshots[0].id == snapshot.id
    # 7.8M + 8.5M + 5.4M + 1.2M + 2.0M cash = 24.9M
    assert snapshot.total_value == Decimal("24900000")


def test_import_over_limit_csv_flags_single_position_alert(
    db_session: Session, account_id
) -> None:
    rows = load_portfolio_csv(FIXTURES / "sample_positions_over_limit.csv")
    service = PortfolioService(db_session)

    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
    )

    summary = service.get_portfolio_summary(account_id)
    assert "TSLA" in summary.over_single_limit_tickers
    assert "NVDA" not in summary.over_single_limit_tickers


def test_second_import_updates_positions_without_creating_duplicates(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    rows_v1 = load_portfolio_csv(FIXTURES / "sample_portfolio_snapshot.csv")
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 10),
        rows=rows_v1,
    )

    # Re-import the same tickers with different market values to confirm
    # upsert-on-(account_id, ticker) rather than duplicate rows.
    rows_v2 = [
        # bump TSLA to a value that should also cross the 1천만원 limit
        type(rows_v1[0])(
            ticker="TSLA",
            quantity=Decimal("30"),
            market_value=Decimal("11500000"),
            sector="Consumer Discretionary",
            theme="musk_ecosystem",
            strategy_type="swing",
        ),
    ]
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows_v2,
    )

    positions = PositionRepository(db_session).list_for_account(account_id)
    tsla = next(p for p in positions if p.ticker == "TSLA")
    assert tsla.market_value == Decimal("11500000")

    snapshots = PortfolioRepository(db_session).list_for_account(account_id)
    assert len(snapshots) == 2  # two snapshot rows, one per date


def test_reimport_same_date_csv_updates_snapshot_without_duplicates(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    rows = load_portfolio_csv(FIXTURES / "sample_portfolio_snapshot.csv")

    first = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("1000000"),
    )

    second = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("2000000"),
    )

    snapshots = PortfolioRepository(db_session).list_for_account(account_id)

    assert len(snapshots) == 1
    assert first.id == second.id
    assert snapshots[0].cash_value == Decimal("2000000")
