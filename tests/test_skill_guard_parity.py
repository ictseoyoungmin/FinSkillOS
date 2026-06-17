"""Parity gate for guards converted to declarative skills behind the seam (20.2b).

Each converted skill must reproduce its guard byte-for-byte across the band
boundaries + edge cases, evaluated through the shared
``context_from_guard_input`` snapshot the live registry uses.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from finskillos.guards import cash_ratio_guard, goal_guard
from finskillos.guards.base import GuardInput
from finskillos.skills.library.cash_ratio_skill import CASH_RATIO_SKILL
from finskillos.skills.library.goal_skill import GOAL_SKILL
from finskillos.skills.risk_registry import context_from_guard_input
from finskillos.skills.runner import run_skill


def _gi(**overrides) -> GuardInput:
    base = dict(
        account_id=uuid.uuid4(),
        total_value=Decimal("100"),
        cash_value=Decimal("20"),
        target_value=Decimal("0"),
        peak_value=None,
        drawdown_pct=None,
        positions=(),
        goal_progress_pct=None,
    )
    base.update(overrides)
    return GuardInput(**base)


def _assert_parity(skill, guard_module, gi: GuardInput) -> None:
    guard_result = guard_module.evaluate(gi)
    skill_result, _ = run_skill(skill, context_from_guard_input(gi))
    assert skill_result.status == guard_result.status
    assert skill_result.risk_level == guard_result.risk_level
    assert skill_result.title == guard_result.title
    assert skill_result.message == guard_result.message
    assert skill_result.watch_next == guard_result.watch_next
    assert skill_result.evidence == guard_result.evidence


@pytest.mark.parametrize(
    "progress",
    [None, "0", "50", "69.9", "70", "85", "89.9", "90", "95", "99.9", "100", "120"],
)
def test_goal_skill_parity(progress):
    gi = _gi(
        goal_progress_pct=Decimal(progress) if progress is not None else None
    )
    _assert_parity(GOAL_SKILL, goal_guard, gi)


@pytest.mark.parametrize(
    "cash,total,min_ratio",
    [
        ("20", "100", "0.10"),   # ratio 0.20 >= min → PASS
        ("10", "100", "0.10"),   # ratio 0.10 == min → PASS (boundary)
        ("7", "100", "0.10"),    # 0.07 in [floor, min) → WARN
        ("5", "100", "0.10"),    # 0.05 == floor → WARN (boundary)
        ("3", "100", "0.10"),    # 0.03 < floor → FAIL
        ("0", "100", "0.10"),    # 0 cash → FAIL
        ("0", "0", "0.10"),      # total 0 → INFO fallback
        ("15", "100", "0.20"),   # ratio 0.15 < min 0.20 but >= floor → WARN
    ],
)
def test_cash_ratio_skill_parity(cash, total, min_ratio):
    gi = _gi(
        cash_value=Decimal(cash),
        total_value=Decimal(total),
        min_cash_ratio=Decimal(min_ratio),
    )
    _assert_parity(CASH_RATIO_SKILL, cash_ratio_guard, gi)
