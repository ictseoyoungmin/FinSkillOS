"""Skill library — one module per skill spec (Phase 20)."""

from finskillos.skills.library.cash_ratio_skill import CASH_RATIO_SKILL
from finskillos.skills.library.concentration_hhi_skill import (
    CONCENTRATION_HHI_SKILL,
)
from finskillos.skills.library.drawdown_skill import DRAWDOWN_SKILL
from finskillos.skills.library.goal_skill import GOAL_SKILL

__all__ = [
    "CASH_RATIO_SKILL",
    "CONCENTRATION_HHI_SKILL",
    "DRAWDOWN_SKILL",
    "GOAL_SKILL",
]
