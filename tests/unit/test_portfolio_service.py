"""Slice 03 — PortfolioService tests.

Covers:
* import_snapshot (PORT-AC-001): positions + portfolio_snapshots upserted
* get_portfolio_summary: total_value, position_count, largest weight,
  single-position 1천만원 limit detection (PORT-AC-003)
* calculate_exposure: sector share map (Risk Firewall feed)
* upsert_position: idempotent updates, no duplicate row creation
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository
from finskillos.services.portfolio_service import (
    SINGLE_POSITION_LIMIT_KRW,
    PortfolioPositionInput,
    PortfolioService,
    load_portfolio_csv,
)


@pytest.fixture
def account_id(db_session: Session):
    return AccountRepository(db_session).create(
        name="Portfolio Account",
        target_value=Decimal("100000000"),
    ).id


def _row(ticker: str, market_value: str, **kw) -> PortfolioPositionInput:
    return PortfolioPositionInput(
        ticker=ticker,
        quantity=Decimal(kw.get("quantity", "1")),
        market_value=Decimal(market_value),
        sector=kw.get("sector"),
        theme=kw.get("theme"),
        strategy_type=kw.get("strategy_type", "swing"),
    )


def test_import_snapshot_creates_positions_and_snapshot(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)

    rows = [
        _row("TSLA", "7800000", sector="EV"),
        _row("NVDA", "8500000", sector="Semiconductors"),
        _row("RKLB", "5400000", sector="Aerospace"),
    ]

    snapshot = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=rows,
        cash_value=Decimal("3000000"),
    )

    assert snapshot.total_value == Decimal("24700000")  # 7.8 + 8.5 + 5.4 + 3.0
    positions = service.get_current_positions(account_id)
    assert {p.ticker for p in positions} == {"TSLA", "NVDA", "RKLB"}


def test_import_snapshot_is_idempotent_per_ticker(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 10),
        rows=[_row("TSLA", "7000000", sector="EV")],
    )
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[_row("TSLA", "7800000", sector="EV")],
    )

    positions = service.get_current_positions(account_id)
    assert len(positions) == 1
    assert positions[0].market_value == Decimal("7800000")


def test_portfolio_summary_reports_total_and_largest_weight(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[
            _row("TSLA", "8000000", sector="EV"),
            _row("NVDA", "2000000", sector="Semiconductors"),
        ],
        cash_value=Decimal("0"),
    )

    summary = service.get_portfolio_summary(account_id)

    assert summary.total_value == Decimal("10000000")
    assert summary.position_count == 2
    assert summary.largest_position_ticker == "TSLA"
    assert summary.largest_position_weight == Decimal("0.8")


def test_portfolio_summary_flags_over_single_position_limit(
    db_session: Session, account_id
) -> None:
    # PORT-AC-003: TSLA market_value=11,000,000 vs limit 10,000,000 → flagged.
    service = PortfolioService(db_session)
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[
            _row("TSLA", "11000000", sector="EV"),
            _row("NVDA", "4800000", sector="Semiconductors"),
        ],
    )

    summary = service.get_portfolio_summary(account_id)

    assert "TSLA" in summary.over_single_limit_tickers
    assert "NVDA" not in summary.over_single_limit_tickers
    assert SINGLE_POSITION_LIMIT_KRW == Decimal("10000000")


def test_calculate_exposure_returns_sector_shares(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[
            _row("TSLA", "4000000", sector="EV"),
            _row("NVDA", "4000000", sector="Semiconductors"),
            _row("PLTR", "2000000", sector="Semiconductors"),
        ],
    )

    exposure = service.calculate_exposure(account_id)

    assert exposure["EV"] == Decimal("0.4")
    assert exposure["Semiconductors"] == Decimal("0.6")


def test_empty_account_summary_does_not_divide_by_zero(
    db_session: Session, account_id
) -> None:
    summary = PortfolioService(db_session).get_portfolio_summary(account_id)

    assert summary.total_value == Decimal("0")
    assert summary.position_count == 0
    assert summary.largest_position_ticker is None
    assert summary.largest_position_weight == Decimal("0")


def test_load_portfolio_csv_accepts_sample_fixture(tmp_path) -> None:
    # The sample fixture is the v2.1 doc-format CSV (ticker column, decimal values).
    from pathlib import Path

    sample = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "portfolio"
        / "sample_portfolio_snapshot.csv"
    )
    rows = load_portfolio_csv(sample)

    tickers = {row.ticker for row in rows}
    assert tickers == {"TSLA", "NVDA", "RKLB", "PLTR"}
    tsla = next(row for row in rows if row.ticker == "TSLA")
    assert tsla.market_value == Decimal("7800000")
    assert tsla.sector == "Consumer Discretionary"


def test_import_snapshot_same_date_updates_existing_snapshot(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)

    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[_row("TSLA", "7000000", sector="EV")],
        cash_value=Decimal("1000000"),
    )

    updated_snapshot = service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[
            _row("TSLA", "8000000", sector="EV"),
            _row("NVDA", "2000000", sector="Semiconductors"),
        ],
        cash_value=Decimal("3000000"),
    )

    snapshots = service.portfolio_repo.list_for_account(account_id)

    assert len(snapshots) == 1
    assert snapshots[0].id == updated_snapshot.id
    assert snapshots[0].total_value == Decimal("13000000")
    assert snapshots[0].cash_value == Decimal("3000000")

    positions = service.get_current_positions(account_id)
    assert {p.ticker for p in positions} == {"TSLA", "NVDA"}


def test_import_snapshot_different_dates_keeps_separate_rows(
    db_session: Session, account_id
) -> None:
    service = PortfolioService(db_session)

    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 10),
        rows=[_row("TSLA", "7000000", sector="EV")],
    )
    service.import_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        rows=[_row("TSLA", "8000000", sector="EV")],
    )

    snapshots = service.portfolio_repo.list_for_account(account_id)
    assert len(snapshots) == 2


def test_load_portfolio_csv_falls_back_to_legacy_symbol_column(tmp_path) -> None:
    legacy = tmp_path / "legacy.csv"
    legacy.write_text("symbol,quantity,market_value\nTSLA,5,2000000\n")

    rows = load_portfolio_csv(legacy)

    assert rows[0].ticker == "TSLA"
    assert rows[0].market_value == Decimal("2000000")
