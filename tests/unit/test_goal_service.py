"""Slice 03 — DB-backed `GoalService` tests.

Verifies that GoalService correctly loads the latest snapshot and
target_value, applies the OS-style phase logic, and handles the empty /
overshoot edge cases per docs/v2_1/09 GOAL-AC-001 and GOAL-AC-002.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.repositories import AccountRepository, PortfolioRepository
from finskillos.services.goal_service import GoalService


def _make_account_with_snapshot(session: Session, total_value: Decimal | None):
    accounts = AccountRepository(session)
    portfolios = PortfolioRepository(session)
    account = accounts.create(
        name="Goal Account",
        target_value=Decimal("100000000"),
    )
    if total_value is not None:
        portfolios.create_snapshot(
            account_id=account.id,
            snapshot_date=date(2026, 5, 17),
            total_value=total_value,
        )
    return account


@pytest.mark.parametrize(
    "total_value,expected_mode,expected_pct",
    [
        (Decimal("49000000"), "GROWTH", Decimal("49.00")),
        (Decimal("57000000"), "BALANCED", Decimal("57.00")),
        (Decimal("85000000"), "PROTECTION", Decimal("85.00")),
        (Decimal("96000000"), "COMPLETION_GUARD", Decimal("96.00")),
        (Decimal("100000000"), "CHALLENGE_COMPLETE", Decimal("100.00")),
    ],
)
def test_goal_service_resolves_mode_from_latest_snapshot(
    db_session: Session,
    total_value: Decimal,
    expected_mode: str,
    expected_pct: Decimal,
) -> None:
    account = _make_account_with_snapshot(db_session, total_value)
    service = GoalService(db_session)

    status = service.get_goal_status(account.id)

    assert status.goal_mode == expected_mode
    assert status.progress_pct == expected_pct
    assert status.target_value == Decimal("100000000")


def test_goal_service_picks_the_most_recent_snapshot(db_session: Session) -> None:
    accounts = AccountRepository(db_session)
    portfolios = PortfolioRepository(db_session)
    account = accounts.create(name="Latest Wins", target_value=Decimal("100000000"))

    portfolios.create_snapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 10),
        total_value=Decimal("57000000"),
    )
    portfolios.create_snapshot(
        account_id=account.id,
        snapshot_date=date(2026, 5, 17),
        total_value=Decimal("85000000"),
    )

    status = GoalService(db_session).get_goal_status(account.id)

    assert status.current_value == Decimal("85000000")
    assert status.goal_mode == "PROTECTION"


def test_goal_service_handles_account_with_no_snapshots(db_session: Session) -> None:
    account = _make_account_with_snapshot(db_session, total_value=None)

    status = GoalService(db_session).get_goal_status(account.id)

    # Empty portfolio: current = 0, no division errors, GROWTH mode by default.
    assert status.current_value == Decimal("0")
    assert status.progress_pct == Decimal("0.00")
    assert status.goal_mode == "GROWTH"
    assert status.early_stop_triggered is False


def test_goal_service_completion_triggers_early_stop(db_session: Session) -> None:
    # GOAL-AC-002: total_value >= 100M ⇒ CHALLENGE_COMPLETE + early_stop_triggered.
    account = _make_account_with_snapshot(db_session, Decimal("105000000"))

    status = GoalService(db_session).get_goal_status(account.id)

    assert status.goal_mode == "CHALLENGE_COMPLETE"
    assert status.early_stop_triggered is True
    assert status.progress_pct == Decimal("100.00")  # saturated


def test_goal_service_unknown_account_raises(db_session: Session) -> None:
    import uuid

    service = GoalService(db_session)
    with pytest.raises(LookupError):
        service.get_goal_status(uuid.uuid4())
