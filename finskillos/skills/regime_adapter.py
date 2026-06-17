"""RegimeBackedSkill — REGIME domain seam into the Skill Layer (Phase 20.3a).

The regime engine is a *classifier* (``RegimeInput → RegimeOutput`` with a regime
state, decision mode, confidence, and prose), structurally different from the
guard verdict ladder. This seam wraps ``classify_regime`` as a classification
skill so REGIME runs through the same runner + audit trail as RISK, with the
regime state carried in ``SkillResult.label`` and the rule version in the audit.
The declarative conversion of ``_classify_state`` follows behind the seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from finskillos.guards.base import STATUS_INFO
from finskillos.regime.regime_engine import RegimeInput, RegimeOutput, classify_regime
from finskillos.skills.base import SkillContext, SkillResult, SkillRunRecord
from finskillos.skills.runner import audit_record
from finskillos.skills.safety import assert_skill_safe

SKILL_ID = "REGIME.CLASSIFY"

# RegimeOutput.risk_level uses the GREEN/YELLOW/ORANGE/RED/UNKNOWN vocabulary the
# SkillResult already shares with the guard ladder.


def _to_result(output: RegimeOutput) -> SkillResult:
    evidence: dict[str, object] = {
        "regime": output.regime,
        "decision_mode": output.decision_mode,
        "confidence": output.confidence,
        "what_it_means": output.what_it_means,
        "positive_factors": list(output.positive_factors),
        "risk_factors": list(output.risk_factors),
        **output.evidence,
    }
    return SkillResult(
        skill_id=SKILL_ID,
        version=output.rule_version,
        status=STATUS_INFO,
        risk_level=output.risk_level,
        title=output.summary,
        message=output.what_happened,
        evidence=evidence,
        watch_next=tuple(output.watch_next),
        fired_rule_ids=(f"{SKILL_ID}-{output.regime}",),
        label=output.regime,
    )


@dataclass(frozen=True)
class RegimeBackedSkill:
    """Registry-compatible classification skill backed by ``classify_regime``."""

    skill_id: str = SKILL_ID

    @property
    def version(self) -> str:
        # The live rule version is carried per-result; expose the engine default
        # for registry listing.
        from finskillos.regime.regime_rules import RULE_VERSION

        return RULE_VERSION

    def run(
        self, ctx: SkillContext, *, now: datetime | None = None
    ) -> tuple[SkillResult, SkillRunRecord]:
        regime_input = ctx.get("regime_input")
        if not isinstance(regime_input, RegimeInput):
            raise TypeError("REGIME skill context is missing a RegimeInput")
        result = _to_result(classify_regime(regime_input))
        assert_skill_safe(result)
        return result, audit_record(result, now=now)
