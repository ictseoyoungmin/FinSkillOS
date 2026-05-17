"""Pure goal-progress calculator.

This module is intentionally DB-free. `finskillos.services.goal_service`
loads the latest portfolio snapshot via SQLAlchemy and forwards
`(total_value, target_value)` here. Slice 03 thresholds:

| range            | mode                |
|------------------|---------------------|
| 0%   – 50%       | GROWTH              |
| 50%  – 80%       | BALANCED            |
| 80%  – 95%       | PROTECTION          |
| 95%  – 100%      | COMPLETION_GUARD    |
| ≥ 100%           | CHALLENGE_COMPLETE  |

`progress_pct` is returned as a 0–100 Decimal; `progress_ratio` is the
matching 0–1 form. Both saturate at 100/1.0 once the target is reached so
overshoot is treated as completion, not as a continued race.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

THRESHOLD_BALANCED = Decimal("0.5")
THRESHOLD_PROTECTION = Decimal("0.8")
THRESHOLD_COMPLETION_GUARD = Decimal("0.95")
THRESHOLD_CHALLENGE_COMPLETE = Decimal("1.0")

GOAL_MODE_GROWTH = "GROWTH"
GOAL_MODE_BALANCED = "BALANCED"
GOAL_MODE_PROTECTION = "PROTECTION"
GOAL_MODE_COMPLETION_GUARD = "COMPLETION_GUARD"
GOAL_MODE_CHALLENGE_COMPLETE = "CHALLENGE_COMPLETE"


@dataclass(frozen=True)
class GoalStatus:
    """Plain-data goal progress reading.

    Field naming matches the slice-03 core-output JSON contract so this
    object can be serialized straight to the Mission Control read model.
    """

    current_value: Decimal
    target_value: Decimal
    progress_ratio: Decimal
    progress_pct: Decimal
    remaining_value: Decimal
    goal_mode: str
    early_stop_triggered: bool


def goal_mode_for(progress_ratio: Decimal) -> str:
    """Return the OS-style goal mode for the given 0-1 progress ratio."""
    if progress_ratio >= THRESHOLD_CHALLENGE_COMPLETE:
        return GOAL_MODE_CHALLENGE_COMPLETE
    if progress_ratio >= THRESHOLD_COMPLETION_GUARD:
        return GOAL_MODE_COMPLETION_GUARD
    if progress_ratio >= THRESHOLD_PROTECTION:
        return GOAL_MODE_PROTECTION
    if progress_ratio >= THRESHOLD_BALANCED:
        return GOAL_MODE_BALANCED
    return GOAL_MODE_GROWTH


def calculate_goal_status(
    current_value: Decimal, target_value: Decimal
) -> GoalStatus:
    """Compute progress, remaining amount, and goal mode."""
    if target_value <= 0:
        raise ValueError("target_value must be positive")

    raw_ratio = Decimal(current_value) / Decimal(target_value)
    # Saturate at 1.0 for the displayed ratio/percentage so the dashboard
    # does not show 137% when the user overshoots — Mission Control treats
    # "≥ target" as CHALLENGE_COMPLETE regardless of magnitude.
    progress_ratio = max(Decimal("0"), min(raw_ratio, Decimal("1")))
    progress_pct = (progress_ratio * Decimal("100")).quantize(Decimal("0.01"))
    remaining_value = max(Decimal("0"), Decimal(target_value) - Decimal(current_value))
    mode = goal_mode_for(raw_ratio)

    return GoalStatus(
        current_value=Decimal(current_value),
        target_value=Decimal(target_value),
        progress_ratio=progress_ratio,
        progress_pct=progress_pct,
        remaining_value=remaining_value,
        goal_mode=mode,
        early_stop_triggered=(mode == GOAL_MODE_CHALLENGE_COMPLETE),
    )
