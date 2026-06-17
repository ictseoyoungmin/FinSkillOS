"""Core types for the v4.3 Skill Layer (Phase 20).

A **Skill** is a versioned, declarative, auditable rule pack. It reads a pure
read-model snapshot (``SkillContext``) the service assembles — never a DB
session — runs an ordered rule ladder (first matching rung wins), and emits a
``SkillResult`` in the v4.2 evidence shape plus a ``SkillRunRecord`` audit row.

Design rules (carried from ``guards.base``):

* Pure + deterministic — same context always yields the same result.
* Descriptive-only — every ``SkillResult`` is safety-scanned centrally by the
  runner; no skill can leak buy/sell wording.
* No DB inside a skill — the runner is handed a snapshot.

See ``docs/v4/PHASE_20_Skill_Layer.md``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Final

# Status + risk vocabularies are shared with the guard ladder so a migrated
# skill is byte-for-byte comparable to the guard it replaces.
from finskillos.guards.base import (  # noqa: F401  (re-exported vocab)
    ALL_RISK_LEVELS,
    ALL_STATUSES,
    RISK_GREEN,
    RISK_UNKNOWN,
    STATUS_INFO,
    STATUS_PASS,
)

# A rule's dynamic fields receive the (already derive-enriched) context.
MessageFn = Callable[["SkillContext"], str]
EvidenceFn = Callable[["SkillContext"], dict[str, object]]
PredicateFn = Callable[["SkillContext"], bool]
DeriveFn = Callable[["SkillContext"], Mapping[str, object]]


@dataclass(frozen=True)
class SkillContext:
    """Pure read snapshot a skill evaluates against.

    ``values`` is the flat feature map the service assembled (the generalised
    ``GuardInput``). ``derive`` output is merged in by the runner before the
    ladder runs, so signal-style computed features (e.g. a resolved drawdown_pct)
    are addressable by the same key lookup.
    """

    values: Mapping[str, object] = field(default_factory=dict)

    def get(self, key: str) -> object | None:
        return self.values.get(key)

    def num(self, key: str) -> Decimal | None:
        """Return ``values[key]`` as Decimal, or None if absent/non-numeric."""
        raw = self.values.get(key)
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def merged(self, extra: Mapping[str, object]) -> SkillContext:
        merged: dict[str, object] = dict(self.values)
        merged.update(extra)
        return SkillContext(values=merged)


@dataclass(frozen=True)
class Rule:
    """One rung of a skill's rule ladder.

    The runner evaluates ladder rungs top-to-bottom and the first whose
    ``when`` returns True produces the result. ``message`` / ``evidence`` may be
    plain values or callables of the context.
    """

    rule_id: str
    when: PredicateFn
    # status / risk_level are usually fixed per rung, but may be callables of the
    # context for categorical guards whose severity is data-derived (e.g. a regime
    # risk level that maps to RED or ORANGE).
    status: str | Callable[[SkillContext], str]
    risk_level: str | Callable[[SkillContext], str]
    title: str
    message: str | MessageFn = ""
    evidence: EvidenceFn | None = None
    watch_next: tuple[str, ...] = ()
    # Classification category for this rung (declarative classification skills);
    # verdict rungs leave it empty. Surfaced on SkillResult.label.
    label: str | Callable[[SkillContext], str] = ""


@dataclass(frozen=True)
class SkillSpec:
    """A declarative, versioned skill."""

    skill_id: str
    version: str
    title: str
    reads: tuple[str, ...]
    ladder: tuple[Rule, ...]
    fallback: Rule
    derive: DeriveFn | None = None
    safety: str = "descriptive-only"


@dataclass(frozen=True)
class SkillResult:
    """Skill output in the v4.2 evidence shape.

    Field names align with ``guards.base.GuardResult`` (title/message/evidence/
    watch_next) so the central safety scan and the cockpit panels treat both
    uniformly; ``fired_rule_ids`` is the new audit affordance.
    """

    skill_id: str
    version: str
    status: str
    risk_level: str
    title: str
    message: str
    evidence: dict[str, object] = field(default_factory=dict)
    watch_next: tuple[str, ...] = ()
    fired_rule_ids: tuple[str, ...] = ()
    # Classification skills (e.g. REGIME.*) emit a category label here; guard-style
    # verdict skills leave it empty and rely on status / risk_level.
    label: str = ""


@dataclass(frozen=True)
class SkillRunRecord:
    """Audit-trail row — the revived 'Applied Skill Rules' (v1 §6/§7)."""

    skill_id: str
    version: str
    fired_rule_ids: tuple[str, ...]
    status: str
    risk_level: str
    evidence: dict[str, object]
    ran_at: datetime


# --- Declarative ladder helpers -----------------------------------------

_NEG_INF: Final[Decimal] = Decimal("-1e30")


def band_rule(
    rule_id: str,
    *,
    feature: str,
    at_least: Decimal | str,
    status: str,
    risk_level: str,
    title: str,
    message: str | MessageFn = "",
    evidence: EvidenceFn | None = None,
    watch_next: tuple[str, ...] = (),
    label: str = "",
) -> Rule:
    """Build a threshold rung that fires when ``ctx.num(feature) >= at_least``.

    Ladders are ordered highest-threshold-first, so first-match reproduces an
    ``if value >= a: … elif value >= b: …`` guard ladder exactly. Use
    ``at_least=ANY`` for the always-true floor rung.
    """

    threshold = Decimal(str(at_least))

    def _when(ctx: SkillContext) -> bool:
        value = ctx.num(feature)
        return value is not None and value >= threshold

    return Rule(
        rule_id=rule_id,
        when=_when,
        status=status,
        risk_level=risk_level,
        title=title,
        message=message,
        evidence=evidence,
        watch_next=watch_next,
        label=label,
    )


# Sentinel threshold for the always-true floor rung of a band ladder.
ANY: Final[Decimal] = _NEG_INF
