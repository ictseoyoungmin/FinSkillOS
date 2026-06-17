"""Phase 20.0 — Skill Layer prototype tests.

The headline test is **parity**: the migrated ``RISK.DRAWDOWN`` skill must
reproduce ``guards.drawdown_guard`` exactly across every band boundary and the
missing-data case. Migration is parity-gated, so this is the gate.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from finskillos.guards import drawdown_guard
from finskillos.guards.base import GuardInput
from finskillos.skills import (
    Rule,
    SkillContext,
    SkillRegistry,
    SkillSpec,
    run_skill,
)
from finskillos.skills.library.drawdown_skill import DRAWDOWN_SKILL


def _guard_input(dd, peak, total) -> GuardInput:
    return GuardInput(
        account_id=uuid.uuid4(),
        total_value=Decimal(str(total)) if total is not None else Decimal("0"),
        cash_value=Decimal("0"),
        target_value=Decimal("0"),
        peak_value=Decimal(str(peak)) if peak is not None else None,
        drawdown_pct=Decimal(str(dd)) if dd is not None else None,
        positions=(),
    )


def _skill_ctx(dd, peak, total) -> SkillContext:
    return SkillContext(
        values={
            "drawdown_pct": Decimal(str(dd)) if dd is not None else None,
            "peak_value": Decimal(str(peak)) if peak is not None else None,
            "total_value": Decimal(str(total)) if total is not None else Decimal("0"),
        }
    )


# (drawdown_pct, peak_value, total_value) — covers each band boundary, both the
# direct-drawdown and the derived-from-peak/total path, and the missing case.
PARITY_CASES = [
    ("0", None, 0),
    ("-5", None, 0),       # PASS boundary (>= -5)
    ("-5.01", None, 0),    # WARN -5..-8 (DRAWDOWN-002)
    ("-7", None, 0),
    ("-8", None, 0),       # WARN sub-band boundary (>= -8)
    ("-8.01", None, 0),    # WARN -8..-10 Yellow Alert (DRAWDOWN-003)
    ("-9", None, 0),
    ("-10", None, 0),      # WARN boundary (>= -10)
    ("-10.01", None, 0),   # FAIL / ORANGE
    ("-12", None, 0),
    ("-15", None, 0),      # ORANGE boundary (>= -15)
    ("-15.01", None, 0),   # FAIL / RED
    ("-20", None, 0),
    (None, 100, 90),       # derived -> -10.00 (WARN)
    (None, 100, 80),       # derived -> -20.00 (RED)
    (None, 100, 105),      # derived -> +5.00 (PASS)
    (None, None, 0),       # missing -> fallback INFO/UNKNOWN
    (None, 0, 50),         # peak <= 0 -> fallback
]


@pytest.mark.parametrize("dd,peak,total", PARITY_CASES)
def test_drawdown_skill_matches_legacy_guard(dd, peak, total):
    guard_result = drawdown_guard.evaluate(_guard_input(dd, peak, total))
    skill_result, _record = run_skill(DRAWDOWN_SKILL, _skill_ctx(dd, peak, total))

    assert skill_result.status == guard_result.status
    assert skill_result.risk_level == guard_result.risk_level
    assert skill_result.title == guard_result.title
    assert skill_result.message == guard_result.message
    assert skill_result.watch_next == guard_result.watch_next
    assert skill_result.evidence == guard_result.evidence


def test_audit_trail_records_fired_rule_id():
    result, record = run_skill(DRAWDOWN_SKILL, _skill_ctx("-7", None, 0))
    assert result.fired_rule_ids == ("RISK.DRAWDOWN-002",)
    assert record.skill_id == "RISK.DRAWDOWN"
    assert record.version == DRAWDOWN_SKILL.version
    assert record.fired_rule_ids == ("RISK.DRAWDOWN-002",)
    assert record.status == "WARN"
    assert record.ran_at is not None


def test_missing_data_fires_fallback_rule():
    result, record = run_skill(DRAWDOWN_SKILL, _skill_ctx(None, None, 0))
    assert result.fired_rule_ids == ("RISK.DRAWDOWN-000",)
    assert result.status == "INFO"
    assert result.risk_level == "UNKNOWN"


def test_runner_enforces_descriptive_only_safety():
    bad = SkillSpec(
        skill_id="TEST.BAD",
        version="bad-v0",
        title="bad",
        reads=(),
        ladder=(),
        fallback=Rule(
            rule_id="TEST.BAD-000",
            when=lambda _c: True,
            status="INFO",
            risk_level="UNKNOWN",
            title="지금 매수하세요",  # forbidden directive
            message="x",
        ),
    )
    with pytest.raises(AssertionError):
        run_skill(bad, SkillContext())


def test_registry_run_all_returns_result_and_audit():
    registry = SkillRegistry()
    registry.register(DRAWDOWN_SKILL)
    results, records = registry.run_all(_skill_ctx("-12", None, 0))
    assert len(results) == 1 and len(records) == 1
    assert results[0].skill_id == "RISK.DRAWDOWN"
    assert results[0].risk_level == "ORANGE"
    assert records[0].fired_rule_ids == ("RISK.DRAWDOWN-004",)


def test_drawdown_yellow_alert_sub_band_is_distinct():
    # Slice-283 refinement: -8..-10 fires the distinct Yellow Alert rung while
    # staying WARN/YELLOW (no decision change vs the -5..-8 give-back band).
    soft, _ = run_skill(DRAWDOWN_SKILL, _skill_ctx("-6", None, 0))
    alert, _ = run_skill(DRAWDOWN_SKILL, _skill_ctx("-9", None, 0))
    assert soft.fired_rule_ids == ("RISK.DRAWDOWN-002",)
    assert alert.fired_rule_ids == ("RISK.DRAWDOWN-003",)
    assert soft.status == alert.status == "WARN"
    assert soft.risk_level == alert.risk_level == "YELLOW"
    assert soft.title != alert.title
    assert "Yellow Alert" in alert.title


def test_drawdown_skill_result_passes_guard_forbidden_scan():
    # Every band's copy must stay descriptive — run them all through the runner,
    # which raises if any leaks buy/sell wording.
    for dd, peak, total in PARITY_CASES:
        run_skill(DRAWDOWN_SKILL, _skill_ctx(dd, peak, total))
