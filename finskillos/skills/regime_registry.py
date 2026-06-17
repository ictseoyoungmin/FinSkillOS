"""REGIME-domain skill registry (Phase 20.3a).

Mirrors ``risk_registry`` for the regime classifier: one classification skill
(``REGIME.CLASSIFY``) through the unified runner + audit. Currently the seam over
``classify_regime``; the ``_classify_state`` ladder converts to declarative
classification rungs behind the seam in 20.3b.
"""

from __future__ import annotations

from finskillos.regime.regime_engine import RegimeInput
from finskillos.skills.base import SkillContext
from finskillos.skills.regime_adapter import RegimeBackedSkill
from finskillos.skills.runner import SkillRegistry


def build_regime_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(RegimeBackedSkill())
    return registry


def context_from_regime_input(regime_input: RegimeInput) -> SkillContext:
    """Snapshot for the regime registry — carries the RegimeInput for the seam."""

    return SkillContext(values={"regime_input": regime_input})
