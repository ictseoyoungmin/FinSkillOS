"""Skill library — one module per skill spec (Phase 20)."""

from finskillos.skills.library.cash_ratio_skill import CASH_RATIO_SKILL
from finskillos.skills.library.concentration_hhi_skill import (
    CONCENTRATION_HHI_SKILL,
)
from finskillos.skills.library.concentration_skill import CONCENTRATION_SKILL
from finskillos.skills.library.drawdown_skill import DRAWDOWN_SKILL
from finskillos.skills.library.event_risk_skill import EVENT_RISK_SKILL
from finskillos.skills.library.event_score_skill import EVENT_SCORE_SKILL
from finskillos.skills.library.goal_skill import GOAL_SKILL
from finskillos.skills.library.overheat_skill import OVERHEAT_SKILL
from finskillos.skills.library.regime_skill import REGIME_SKILL
from finskillos.skills.library.single_position_skill import SINGLE_POSITION_SKILL

__all__ = [
    "CASH_RATIO_SKILL",
    "CONCENTRATION_HHI_SKILL",
    "CONCENTRATION_SKILL",
    "DRAWDOWN_SKILL",
    "EVENT_RISK_SKILL",
    "EVENT_SCORE_SKILL",
    "GOAL_SKILL",
    "OVERHEAT_SKILL",
    "REGIME_SKILL",
    "SINGLE_POSITION_SKILL",
]
