"""GuardBackedSkill — the Strangler-Fig seam (Phase 20.1).

Wraps a not-yet-declarative guard's pure ``evaluate(GuardInput) -> GuardResult``
as a first-class Skill, so every guard runs through the unified registry + audit
trail *now*, while each guard is converted to a declarative ``SkillSpec`` behind
the seam incrementally (parity-gated). Parity is exact by construction here — the
skill *is* the guard.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from finskillos.guards.base import GuardInput, GuardResult
from finskillos.skills.base import SkillContext, SkillResult, SkillRunRecord
from finskillos.skills.runner import audit_record
from finskillos.skills.safety import assert_skill_safe

# The synthetic Rule ID a guard-backed skill reports until the guard is rewritten
# as an explicit ladder. The status carried alongside keeps the audit meaningful.
_RUN_SUFFIX = "-RUN"


@dataclass(frozen=True)
class GuardBackedSkill:
    """A registry-compatible skill backed by an existing guard function."""

    skill_id: str
    version: str
    guard_evaluate: Callable[[GuardInput], GuardResult]
    # How to recover the GuardInput from the shared SkillContext. Defaults to the
    # ``guard_input`` value the service stashes on the context.
    to_input: Callable[[SkillContext], GuardInput] = lambda ctx: ctx.get(  # type: ignore[assignment]
        "guard_input"
    )

    def run(
        self, ctx: SkillContext, *, now: datetime | None = None
    ) -> tuple[SkillResult, SkillRunRecord]:
        guard_result = self.guard_evaluate(self.to_input(ctx))
        result = SkillResult(
            skill_id=self.skill_id,
            version=self.version,
            status=guard_result.status,
            risk_level=guard_result.risk_level,
            title=guard_result.title,
            message=guard_result.message,
            evidence=dict(guard_result.evidence),
            watch_next=tuple(guard_result.watch_next),
            fired_rule_ids=(f"{self.skill_id}{_RUN_SUFFIX}",),
        )
        # Same descriptive-only contract as every other skill.
        assert_skill_safe(result)
        return result, audit_record(result, now=now)
