"""Slice 02 — repository CRUD tests.

Covers create/read/update/delete and resolve flow for every slice-02
repository, plus the idempotent seed helper.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    PortfolioRepository,
    PositionRepository,
    TradeRepository,
)
from finskillos.db.seed import seed_default_account


@pytest.fixture
def account_id(db_session: Session):
    repo = AccountRepository(db_session)
    account = repo.create(
        name="Main Trading Account",
        target_value=Decimal("100000000"),
        base_currency="KRW",
    )
    return account.id


def test_account_repository_crud(db_session: Session) -> None:
    repo = AccountRepository(db_session)

    created = repo.create(
        name="Alpha Account",
        target_value=Decimal("80000000"),
    )
    assert created.id is not None

    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.name == "Alpha Account"

    by_name = repo.get_by_name("Alpha Account")
    assert by_name is not None and by_name.id == created.id

    updated = repo.update_target(created.id, Decimal("90000000"))
    assert updated.target_value == Decimal("90000000")

    repo.delete(created.id)
    assert repo.get(created.id) is None


def test_position_repository_crud(db_session: Session, account_id) -> None:
    repo = PositionRepository(db_session)

    pos = repo.create(
        account_id=account_id,
        ticker="TSLA",
        quantity=Decimal("10"),
        market_value=Decimal("3000000"),
        sector="EV",
        thesis="Long Tesla on Musk ecosystem catalysts",
    )
    assert pos.id is not None
    assert pos.strategy_type == "swing"

    found = repo.get_by_account_and_ticker(account_id, "TSLA")
    assert found is not None and found.id == pos.id

    updated = repo.update_market_value(
        pos.id, market_value=Decimal("3300000"), pnl_pct=Decimal("0.1")
    )
    assert updated.market_value == Decimal("3300000")
    assert updated.pnl_pct == Decimal("0.1")

    repo.delete(pos.id)
    assert repo.get(pos.id) is None


def test_portfolio_repository_latest_returns_most_recent(
    db_session: Session, account_id
) -> None:
    repo = PortfolioRepository(db_session)
    repo.create_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 10),
        total_value=Decimal("56000000"),
    )
    repo.create_snapshot(
        account_id=account_id,
        snapshot_date=date(2026, 5, 17),
        total_value=Decimal("57500000"),
    )

    latest = repo.latest(account_id)
    assert latest is not None
    assert latest.snapshot_date == date(2026, 5, 17)
    assert latest.total_value == Decimal("57500000")


def test_trade_repository_filters_by_date_range(
    db_session: Session, account_id
) -> None:
    repo = TradeRepository(db_session)
    for d, ticker in [
        (date(2026, 5, 10), "TSLA"),
        (date(2026, 5, 12), "NVDA"),
        (date(2026, 5, 17), "RKLB"),
    ]:
        repo.create(
            account_id=account_id,
            ticker=ticker,
            trade_date=d,
            side="BUY",
            quantity=Decimal("1"),
            price=Decimal("100"),
            amount=Decimal("100"),
        )

    in_range = repo.list_for_account(
        account_id, start=date(2026, 5, 12), end=date(2026, 5, 17)
    )
    assert [t.ticker for t in in_range] == ["NVDA", "RKLB"]


def test_alert_repository_resolve_marks_alert_resolved(
    db_session: Session, account_id
) -> None:
    repo = AlertRepository(db_session)

    alert = repo.create(
        account_id=account_id,
        alert_date=date(2026, 5, 17),
        guard_name="MAX_SINGLE_POSITION_VALUE",
        severity="YELLOW",
        title="단일 종목 한도 점검",
        payload={"ticker": "TSLA", "observed": "11000000"},
    )
    active = repo.list_active(account_id=account_id)
    assert len(active) == 1 and active[0].id == alert.id

    resolved = repo.resolve(alert.id)
    assert resolved.resolved is True
    assert resolved.resolved_at is not None

    assert repo.list_active(account_id=account_id) == []


def test_seed_default_account_is_idempotent(
    db_session: Session, clean_env
) -> None:
    first = seed_default_account(db_session)
    assert first.created_account is True
    assert first.created_snapshot is True
    assert first.initial_snapshot is not None
    assert first.initial_snapshot.total_value == Decimal("57000000")
    assert first.account.target_value == Decimal("100000000")
    assert first.account.base_currency == "KRW"

    second = seed_default_account(db_session)
    assert second.created_account is False
    assert second.created_snapshot is False
    assert second.account.id == first.account.id
