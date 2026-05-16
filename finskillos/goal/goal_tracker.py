from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class GoalStatus:
    current_amount: Decimal
    target_amount: Decimal
    progress_ratio: Decimal
    remaining_amount: Decimal
    phase: str


def calculate_goal_status(current_amount: Decimal, target_amount: Decimal) -> GoalStatus:
    if target_amount <= 0:
        raise ValueError("target_amount must be positive")

    progress_ratio = max(Decimal("0"), current_amount / target_amount)
    remaining_amount = max(Decimal("0"), target_amount - current_amount)
    return GoalStatus(
        current_amount=current_amount,
        target_amount=target_amount,
        progress_ratio=progress_ratio,
        remaining_amount=remaining_amount,
        phase=_phase_for(progress_ratio),
    )


def _phase_for(progress_ratio: Decimal) -> str:
    if progress_ratio >= Decimal("1"):
        return "COMPLETE_PROTECTION"
    if progress_ratio >= Decimal("0.9"):
        return "CAPITAL_PROTECTION"
    if progress_ratio >= Decimal("0.5"):
        return "COMPOUNDING"
    return "FOUNDATION"
