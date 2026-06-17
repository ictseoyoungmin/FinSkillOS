"""Phase 20.1 — the RISK registry runs all eight guards through the Skill Layer.

Parity for the guard-backed seam is exact by construction (the skill calls the
guard), but we still assert it end-to-end: the registry's results match running
the guards directly, in the same order, and every run produces an audit record.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from finskillos.guards import (
    cash_ratio_guard,
    concentration_guard,
    drawdown_guard,
    event_risk_guard,
    goal_guard,
    overheat_guard,
    regime_guard,
    single_position_guard,
)
from finskillos.guards.base import GuardInput, PositionRiskInput
from finskillos.skills.risk_registry import (
    SKILL_TO_GUARD_NAME,
    build_risk_registry,
    context_from_guard_input,
)

_LADDER = [
    cash_ratio_guard,
    single_position_guard,
    concentration_guard,
    drawdown_guard,
    goal_guard,
    regime_guard,
    overheat_guard,
    event_risk_guard,
]


def _guard_input() -> GuardInput:
    return GuardInput(
        account_id=uuid.uuid4(),
        total_value=Decimal("50000000"),
        cash_value=Decimal("3000000"),
        target_value=Decimal("100000000"),
        peak_value=Decimal("55000000"),
        drawdown_pct=Decimal("-9.1"),
        positions=(
            PositionRiskInput("AAA", Decimal("12000000"), sector="Tech"),
            PositionRiskInput("BBB", Decimal("8000000"), sector="Tech"),
        ),
        regime="HEALTHY_BULL",
        regime_risk_level="GREEN",
        decision_mode="SELECTIVE_ATTACK",
        goal_progress_pct=Decimal("47"),
    )


def test_registry_runs_skills_in_ladder_order():
    registry = build_risk_registry()
    results, records = registry.run_all(context_from_guard_input(_guard_input()))
    assert len(results) == 9
    assert len(records) == 9
    # First eight mirror the legacy ladder order; HHI is the skill-only ninth.
    assert [r.skill_id for r in results] == [
        "RISK.CASH_RATIO",
        "RISK.SINGLE_POSITION",
        "RISK.SECTOR_CONCENTRATION",
        "RISK.DRAWDOWN",
        "RISK.GOAL_PROTECTION",
        "RISK.REGIME_RISK",
        "RISK.OVERHEAT_ENTRY",
        "RISK.EVENT_RISK",
        "RISK.CONCENTRATION_HHI",
    ]


def test_registry_results_match_running_guards_directly():
    gi = _guard_input()
    registry = build_risk_registry()
    results, _ = registry.run_all(context_from_guard_input(gi))
    # Only the eight guard-derived skills have a direct guard counterpart.
    for skill_result, guard_module in zip(results[:8], _LADDER, strict=True):
        guard_result = guard_module.evaluate(gi)
        assert skill_result.status == guard_result.status
        assert skill_result.risk_level == guard_result.risk_level
        assert skill_result.title == guard_result.title
        assert skill_result.message == guard_result.message
        assert skill_result.watch_next == guard_result.watch_next
        assert skill_result.evidence == guard_result.evidence


def test_every_skill_has_a_guard_name_mapping():
    registry = build_risk_registry()
    for skill in registry.all():
        assert skill.skill_id in SKILL_TO_GUARD_NAME


def test_audit_records_carry_fired_rule_ids():
    registry = build_risk_registry()
    _results, records = registry.run_all(context_from_guard_input(_guard_input()))
    for record in records:
        assert record.fired_rule_ids  # non-empty
        assert record.ran_at is not None
    # All eight RISK guards are declarative now — every fired id is a real ladder
    # rule id under its own skill namespace (no <skill>-RUN seam ids remain).
    for record in records:
        assert record.fired_rule_ids[0].startswith(f"{record.skill_id}-")
        assert not record.fired_rule_ids[0].endswith("-RUN")


def test_service_skill_ladder_maps_to_guard_names_with_audit():
    # Phase 20.2: the service helper maps SkillResults back to GuardResults keyed
    # by canonical guard names, and returns the audit records alongside.
    from finskillos.guards.base import GUARD_DRAWDOWN
    from finskillos.services.risk_guard_service import _run_skill_ladder

    guard_results, records = _run_skill_ladder(_guard_input())
    assert len(guard_results) == 9
    assert len(records) == 9
    names = {g.guard_name for g in guard_results}
    assert GUARD_DRAWDOWN in names
    assert "CONCENTRATION_HHI_GUARD" in names
    assert all(g.guard_name for g in guard_results)
    # Audit + report stay aligned on status per skill.
    for guard_result, record in zip(guard_results, records, strict=True):
        assert guard_result.status == record.status
