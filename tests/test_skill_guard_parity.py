"""Parity gate for guards converted to declarative skills behind the seam (20.2b).

Each converted skill must reproduce its guard byte-for-byte across the band
boundaries + edge cases, evaluated through the shared
``context_from_guard_input`` snapshot the live registry uses.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from finskillos.guards import (
    cash_ratio_guard,
    concentration_guard,
    event_risk_guard,
    goal_guard,
    overheat_guard,
    regime_guard,
    single_position_guard,
)
from finskillos.guards.base import EventRiskSummary, GuardInput, PositionRiskInput
from finskillos.skills.library.cash_ratio_skill import CASH_RATIO_SKILL
from finskillos.skills.library.concentration_skill import CONCENTRATION_SKILL
from finskillos.skills.library.event_risk_skill import EVENT_RISK_SKILL
from finskillos.skills.library.goal_skill import GOAL_SKILL
from finskillos.skills.library.overheat_skill import OVERHEAT_SKILL
from finskillos.skills.library.regime_skill import REGIME_SKILL
from finskillos.skills.library.single_position_skill import SINGLE_POSITION_SKILL
from finskillos.skills.risk_registry import context_from_guard_input
from finskillos.skills.runner import run_skill


def _pos(ticker, mv, sector=None):
    return PositionRiskInput(ticker, Decimal(mv), sector=sector)


def _gi(**overrides) -> GuardInput:
    base = dict(
        account_id=uuid.uuid4(),
        total_value=Decimal("100"),
        cash_value=Decimal("20"),
        target_value=Decimal("0"),
        peak_value=None,
        drawdown_pct=None,
        positions=(),
        goal_progress_pct=None,
    )
    base.update(overrides)
    return GuardInput(**base)


def _assert_parity(skill, guard_module, gi: GuardInput) -> None:
    guard_result = guard_module.evaluate(gi)
    skill_result, _ = run_skill(skill, context_from_guard_input(gi))
    assert skill_result.status == guard_result.status
    assert skill_result.risk_level == guard_result.risk_level
    assert skill_result.title == guard_result.title
    assert skill_result.message == guard_result.message
    assert skill_result.watch_next == guard_result.watch_next
    assert skill_result.evidence == guard_result.evidence


@pytest.mark.parametrize(
    "progress",
    [None, "0", "50", "69.9", "70", "85", "89.9", "90", "95", "99.9", "100", "120"],
)
def test_goal_skill_parity(progress):
    gi = _gi(
        goal_progress_pct=Decimal(progress) if progress is not None else None
    )
    _assert_parity(GOAL_SKILL, goal_guard, gi)


@pytest.mark.parametrize(
    "cash,total,min_ratio",
    [
        ("20", "100", "0.10"),   # ratio 0.20 >= min → PASS
        ("10", "100", "0.10"),   # ratio 0.10 == min → PASS (boundary)
        ("7", "100", "0.10"),    # 0.07 in [floor, min) → WARN
        ("5", "100", "0.10"),    # 0.05 == floor → WARN (boundary)
        ("3", "100", "0.10"),    # 0.03 < floor → FAIL
        ("0", "100", "0.10"),    # 0 cash → FAIL
        ("0", "0", "0.10"),      # total 0 → INFO fallback
        ("15", "100", "0.20"),   # ratio 0.15 < min 0.20 but >= floor → WARN
    ],
)
def test_cash_ratio_skill_parity(cash, total, min_ratio):
    gi = _gi(
        cash_value=Decimal(cash),
        total_value=Decimal(total),
        min_cash_ratio=Decimal(min_ratio),
    )
    _assert_parity(CASH_RATIO_SKILL, cash_ratio_guard, gi)


@pytest.mark.parametrize(
    "regime",
    [
        None,
        "RISK_ON_OVERHEAT",
        "DISTRIBUTION_RISK",
        "HEALTHY_BULL",
        "PANIC",
        "RECOVERY",
    ],
)
def test_overheat_skill_parity(regime):
    gi = _gi(regime=regime, decision_mode="SELECTIVE_ATTACK")
    _assert_parity(OVERHEAT_SKILL, overheat_guard, gi)


@pytest.mark.parametrize(
    "regime,risk_level",
    [
        (None, None),                       # fallback case 1
        ("HEALTHY_BULL", None),             # fallback (level missing)
        ("HEALTHY_BULL", "GREEN"),          # PASS
        ("DISTRIBUTION_RISK", "YELLOW"),    # WARN
        ("RISK_OFF", "ORANGE"),             # FAIL / ORANGE
        ("PANIC", "RED"),                   # FAIL / RED
        ("HEALTHY_BULL", "UNKNOWN"),        # INFO uninterpretable
        ("HEALTHY_BULL", "BOGUS"),          # INFO uninterpretable (unmapped)
    ],
)
def test_regime_skill_parity(regime, risk_level):
    gi = _gi(
        regime=regime,
        regime_risk_level=risk_level,
        decision_mode="HOLD_WINNERS",
    )
    _assert_parity(REGIME_SKILL, regime_guard, gi)


@pytest.mark.parametrize(
    "positions",
    [
        (),                                              # all within → PASS
        (_pos("A", "5000000"),),                         # under limit → PASS
        (_pos("A", "9500000"),),                         # 95% of 10M → approaching WARN
        (_pos("A", "12000000"),),                        # over 10M → FAIL
        (_pos("A", "12000000"), _pos("B", "9200000")),   # over + approaching → FAIL wins
    ],
)
def test_single_position_skill_parity(positions):
    _assert_parity(SINGLE_POSITION_SKILL, single_position_guard, _gi(positions=positions))


@pytest.mark.parametrize(
    "positions",
    [
        (),                                                        # no positions → INFO
        (_pos("A", "0", "Tech"),),                                 # zero value → INFO
        (_pos("A", "30", "Tech"), _pos("B", "70", "Energy")),      # 70% → FAIL
        (_pos("A", "60", "Tech"), _pos("B", "40", "Energy")),      # 60% > 50 → FAIL
        (_pos("A", "40", "Tech"), _pos("B", "60", "Tech")),        # one sector 100% → FAIL
        (_pos("A", "45", "Tech"), _pos("B", "30", "Energy"), _pos("C", "25", "Health")),
        (_pos("A", "30", "Tech"), _pos("B", "30", "Energy"), _pos("C", "40", "Health")),
        (_pos("A", "34", "Tech"), _pos("B", "33", "Energy"), _pos("C", "33", "Health")),
        (_pos("A", "50", None), _pos("B", "50", "Energy")),        # UNCLASSIFIED bucket
        (_pos("A", "60", None), _pos("B", "40", None)),            # all UNCLASSIFIED → INFO
        (_pos("A", "100", None),),                                 # single, UNCLASSIFIED → INFO
    ],
)
def test_concentration_skill_parity(positions):
    _assert_parity(CONCENTRATION_SKILL, concentration_guard, _gi(positions=positions))


@pytest.mark.parametrize(
    "event_risk",
    [
        None,
        EventRiskSummary(connected=False),
        EventRiskSummary(connected=True, upcoming_count=0),
        EventRiskSummary(
            connected=True,
            upcoming_count=3,
            holdings_relevant_count=2,
            highest_label="HIGH",
            highest_score=Decimal("0.82"),
            nearest_days=4,
            affected_tickers=("AAA", "BBB"),
        ),
        EventRiskSummary(connected=True, upcoming_count=1, highest_label="LOW"),
    ],
)
def test_event_risk_skill_parity(event_risk):
    _assert_parity(EVENT_RISK_SKILL, event_risk_guard, _gi(event_risk=event_risk))
