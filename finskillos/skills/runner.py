"""Skill registry + runner — the unified home the empty ``kernel/rule_engine``
stub was always meant to hold (Phase 20).

``run_skill`` resolves derived features, walks the rule ladder (first matching
rung wins), enforces the descriptive-only safety contract centrally, and emits
both the ``SkillResult`` (v4.2 evidence shape) and the ``SkillRunRecord`` audit
row. No DB access — the caller hands in a ``SkillContext`` snapshot.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from finskillos.skills.base import (
    Rule,
    SkillContext,
    SkillResult,
    SkillRunRecord,
    SkillSpec,
)
from finskillos.skills.safety import assert_skill_safe


def _resolve(value, ctx: SkillContext):
    """Call ``value`` with the context if it's a callable, else return it."""
    return value(ctx) if callable(value) else value


def _build_result(spec: SkillSpec, rule: Rule, ctx: SkillContext) -> SkillResult:
    evidence = _resolve(rule.evidence, ctx) if rule.evidence is not None else {}
    return SkillResult(
        skill_id=spec.skill_id,
        version=spec.version,
        status=rule.status,
        risk_level=rule.risk_level,
        title=str(_resolve(rule.title, ctx)),
        message=str(_resolve(rule.message, ctx)),
        evidence=dict(evidence),
        watch_next=tuple(rule.watch_next),
        fired_rule_ids=(rule.rule_id,),
    )


def run_skill(
    spec: SkillSpec,
    ctx: SkillContext,
    *,
    now: datetime | None = None,
) -> tuple[SkillResult, SkillRunRecord]:
    """Evaluate ``spec`` against ``ctx``; return (result, audit record)."""

    if spec.derive is not None:
        ctx = ctx.merged(spec.derive(ctx))

    fired = next((rule for rule in spec.ladder if rule.when(ctx)), spec.fallback)
    result = _build_result(spec, fired, ctx)

    # One safety contract for every skill, enforced before the result leaves.
    assert_skill_safe(result)
    return result, audit_record(result, now=now)


def audit_record(
    result: SkillResult, *, now: datetime | None = None
) -> SkillRunRecord:
    """Build the audit-trail row for a result — shared by declarative skills and
    the guard-backed seam so the 'Applied Skill Rules' log is uniform."""

    return SkillRunRecord(
        skill_id=result.skill_id,
        version=result.version,
        fired_rule_ids=result.fired_rule_ids,
        status=result.status,
        risk_level=result.risk_level,
        evidence=result.evidence,
        ran_at=now or datetime.now(timezone.utc),
    )


class SkillRegistry:
    """In-memory registry of skills, keyed by ``skill_id``.

    Mirrors the guard orchestration's ``(name, evaluate_fn)`` list, so
    ``run_all`` can replace ``_run_all_guards``. A registered skill is either a
    declarative ``SkillSpec`` or any object exposing ``skill_id`` / ``version`` /
    ``run(ctx, *, now)`` (the Strangler-Fig seam — e.g. ``GuardBackedSkill``
    wrapping a not-yet-declarative guard). Both flow through ``run_all``
    identically, producing the same ``SkillResult`` + audit ``SkillRunRecord``.
    """

    def __init__(self) -> None:
        self._skills: dict[str, object] = {}

    def register(self, skill: object) -> None:
        skill_id = skill.skill_id  # type: ignore[attr-defined]
        if skill_id in self._skills:
            raise ValueError(f"skill {skill_id!r} already registered")
        self._skills[skill_id] = skill

    def get(self, skill_id: str) -> object:
        return self._skills[skill_id]

    def all(self) -> tuple[object, ...]:
        return tuple(self._skills.values())

    def run_all(
        self,
        ctx: SkillContext,
        *,
        skill_ids: Iterable[str] | None = None,
        now: datetime | None = None,
    ) -> tuple[tuple[SkillResult, ...], tuple[SkillRunRecord, ...]]:
        skills = (
            [self._skills[s] for s in skill_ids]
            if skill_ids is not None
            else list(self._skills.values())
        )
        results: list[SkillResult] = []
        records: list[SkillRunRecord] = []
        for skill in skills:
            result, record = run_one(skill, ctx, now=now)
            results.append(result)
            records.append(record)
        return tuple(results), tuple(records)


def run_one(
    skill: object,
    ctx: SkillContext,
    *,
    now: datetime | None = None,
) -> tuple[SkillResult, SkillRunRecord]:
    """Evaluate any registered skill — declarative ``SkillSpec`` or a seam object
    exposing ``run(ctx, *, now)``."""

    if isinstance(skill, SkillSpec):
        return run_skill(skill, ctx, now=now)
    return skill.run(ctx, now=now)  # type: ignore[attr-defined]
