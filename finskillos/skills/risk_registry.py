"""RISK-domain skill registry (Phase 20.1).

Assembles the eight live risk guards as Skills so the whole risk ladder runs
through the unified runner + audit trail. ``RISK.DRAWDOWN`` is the fully
declarative skill; the other seven are ``GuardBackedSkill`` seams over their
existing guard functions and convert to declarative specs incrementally behind
the seam (parity-gated). Registration order mirrors the legacy ``_run_all_guards``
ladder so the aggregated report ordering is unchanged.
"""

from __future__ import annotations

from finskillos.guards.base import (
    GUARD_CASH_RATIO,
    GUARD_DRAWDOWN,
    GUARD_EVENT_PLACEHOLDER,
    GUARD_GOAL_PROTECTION,
    GUARD_OVERHEAT_ENTRY,
    GUARD_REGIME_RISK,
    GUARD_SECTOR_CONCENTRATION,
    GUARD_SINGLE_POSITION,
    GuardInput,
)
from finskillos.skills.base import SkillContext
from finskillos.skills.library.cash_ratio_skill import CASH_RATIO_SKILL
from finskillos.skills.library.concentration_skill import CONCENTRATION_SKILL
from finskillos.skills.library.drawdown_skill import DRAWDOWN_SKILL
from finskillos.skills.library.event_risk_skill import EVENT_RISK_SKILL
from finskillos.skills.library.goal_skill import GOAL_SKILL
from finskillos.skills.library.overheat_skill import OVERHEAT_SKILL
from finskillos.skills.library.regime_skill import REGIME_SKILL
from finskillos.skills.library.single_position_skill import SINGLE_POSITION_SKILL
from finskillos.skills.runner import SkillRegistry

# Skill-id ⇄ guard-name map so the service can rebuild a RiskGuardReport keyed by
# the canonical guard names while running everything as skills (Phase 20.2).
SKILL_TO_GUARD_NAME = {
    "RISK.CASH_RATIO": GUARD_CASH_RATIO,
    "RISK.SINGLE_POSITION": GUARD_SINGLE_POSITION,
    "RISK.SECTOR_CONCENTRATION": GUARD_SECTOR_CONCENTRATION,
    "RISK.DRAWDOWN": GUARD_DRAWDOWN,
    "RISK.GOAL_PROTECTION": GUARD_GOAL_PROTECTION,
    "RISK.REGIME_RISK": GUARD_REGIME_RISK,
    "RISK.OVERHEAT_ENTRY": GUARD_OVERHEAT_ENTRY,
    "RISK.EVENT_RISK": GUARD_EVENT_PLACEHOLDER,
}

def build_risk_registry() -> SkillRegistry:
    """Registry of the eight risk skills, in the legacy ladder order.

    All eight are now declarative ``SkillSpec``s (the Strangler-Fig seam is fully
    retired for the RISK domain; ``GuardBackedSkill`` remains available for future
    domains). Each is parity-tested against its originating guard.
    """

    registry = SkillRegistry()
    registry.register(CASH_RATIO_SKILL)
    registry.register(SINGLE_POSITION_SKILL)
    registry.register(CONCENTRATION_SKILL)
    registry.register(DRAWDOWN_SKILL)
    registry.register(GOAL_SKILL)
    registry.register(REGIME_SKILL)
    registry.register(OVERHEAT_SKILL)
    registry.register(EVENT_RISK_SKILL)
    return registry


def context_from_guard_input(guard_input: GuardInput) -> SkillContext:
    """Shared snapshot for the risk registry.

    Carries the original ``GuardInput`` for guard-backed skills *and* the flat
    features the declarative ``RISK.DRAWDOWN`` skill reads — one context drives
    both kinds of skill.
    """

    return SkillContext(
        values={
            "guard_input": guard_input,
            "account_id": guard_input.account_id,
            "total_value": guard_input.total_value,
            "cash_value": guard_input.cash_value,
            "target_value": guard_input.target_value,
            "peak_value": guard_input.peak_value,
            "drawdown_pct": guard_input.drawdown_pct,
            "positions": guard_input.positions,
            "regime": guard_input.regime,
            "regime_risk_level": guard_input.regime_risk_level,
            "decision_mode": guard_input.decision_mode,
            "goal_progress_pct": guard_input.goal_progress_pct,
            "single_position_limit": guard_input.single_position_limit,
            "min_cash_ratio": guard_input.min_cash_ratio,
            "event_risk": guard_input.event_risk,
        }
    )
