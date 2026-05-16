from decimal import Decimal

import pytest

from finskillos.goal.goal_tracker import calculate_goal_status


def test_goal_status_calculates_progress_and_remaining_amount() -> None:
    status = calculate_goal_status(Decimal("25000000"), Decimal("100000000"))

    assert status.progress_ratio == Decimal("0.25")
    assert status.remaining_amount == Decimal("75000000")
    assert status.phase == "FOUNDATION"


def test_goal_status_enters_protection_near_target() -> None:
    status = calculate_goal_status(Decimal("92000000"), Decimal("100000000"))

    assert status.phase == "CAPITAL_PROTECTION"


def test_goal_status_rejects_invalid_target() -> None:
    with pytest.raises(ValueError):
        calculate_goal_status(Decimal("1"), Decimal("0"))
