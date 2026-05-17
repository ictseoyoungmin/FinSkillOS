"""Slice 03 — pure goal-tracker tests.

These exercise the OS-style threshold table from `.devmd/03` directly
(no DB):

| range            | mode                |
|------------------|---------------------|
| 0%   – 50%       | GROWTH              |
| 50%  – 80%       | BALANCED            |
| 80%  – 95%       | PROTECTION          |
| 95%  – 100%      | COMPLETION_GUARD    |
| ≥ 100%           | CHALLENGE_COMPLETE  |
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from finskillos.goal.goal_tracker import (
    calculate_goal_status,
    goal_mode_for,
)


@pytest.mark.parametrize(
    "current,expected_mode,expected_pct",
    [
        (Decimal("49000000"), "GROWTH", Decimal("49.00")),
        (Decimal("57000000"), "BALANCED", Decimal("57.00")),
        (Decimal("85000000"), "PROTECTION", Decimal("85.00")),
        (Decimal("96000000"), "COMPLETION_GUARD", Decimal("96.00")),
        (Decimal("100000000"), "CHALLENGE_COMPLETE", Decimal("100.00")),
    ],
)
def test_calculate_goal_status_threshold_table(
    current: Decimal, expected_mode: str, expected_pct: Decimal
) -> None:
    status = calculate_goal_status(current, Decimal("100000000"))

    assert status.goal_mode == expected_mode
    assert status.progress_pct == expected_pct


def test_calculate_goal_status_returns_remaining_value() -> None:
    status = calculate_goal_status(Decimal("57000000"), Decimal("100000000"))

    assert status.remaining_value == Decimal("43000000")
    assert status.progress_ratio == Decimal("0.57")
    assert status.early_stop_triggered is False


def test_calculate_goal_status_saturates_overshoot() -> None:
    status = calculate_goal_status(Decimal("137000000"), Decimal("100000000"))

    assert status.goal_mode == "CHALLENGE_COMPLETE"
    assert status.progress_pct == Decimal("100.00")
    assert status.progress_ratio == Decimal("1")
    assert status.remaining_value == Decimal("0")
    assert status.early_stop_triggered is True


def test_goal_mode_for_at_lower_boundaries() -> None:
    # Exactly 50% goes to BALANCED, not GROWTH (range is [0.5, 0.8))
    assert goal_mode_for(Decimal("0.5")) == "BALANCED"
    assert goal_mode_for(Decimal("0.799999")) == "BALANCED"
    assert goal_mode_for(Decimal("0.8")) == "PROTECTION"
    assert goal_mode_for(Decimal("0.95")) == "COMPLETION_GUARD"
    assert goal_mode_for(Decimal("1")) == "CHALLENGE_COMPLETE"


def test_calculate_goal_status_rejects_invalid_target() -> None:
    with pytest.raises(ValueError):
        calculate_goal_status(Decimal("1"), Decimal("0"))
