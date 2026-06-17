"""Phase 20.4 — EVENT.SCORE labelling matches event_risk_service.risk_label_for_score.

The DB-coupled score assembly stays in the service; this skill is the pure
labelling band ladder, parity-tested against the canonical function.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from finskillos.services.event_risk_service import risk_label_for_score
from finskillos.skills.event_registry import (
    build_event_registry,
    context_from_event_score,
)
from finskillos.skills.runner import run_skill

_LABEL_TO_RISK = {
    "LOW": "GREEN",
    "MODERATE": "YELLOW",
    "HIGH": "ORANGE",
    "CRITICAL": "RED",
}


@pytest.mark.parametrize(
    "score",
    ["0", "1.99", "2.0", "3.99", "4.0", "6.99", "7.0", "8.5", "10"],
)
def test_event_score_label_matches_service(score):
    skill = build_event_registry().get("EVENT.SCORE")
    result, _ = run_skill(skill, context_from_event_score(Decimal(score)))
    expected_label = risk_label_for_score(Decimal(score))
    assert result.label == expected_label
    assert result.risk_level == _LABEL_TO_RISK[expected_label]
    assert result.status == "INFO"
    assert result.fired_rule_ids[0].startswith("EVENT.SCORE-")


def test_event_score_fallback_without_score():
    skill = build_event_registry().get("EVENT.SCORE")
    result, record = run_skill(skill, context_from_event_score(None))
    assert result.fired_rule_ids == ("EVENT.SCORE-000",)
    assert result.label == "UNKNOWN"
    assert record.risk_level == "UNKNOWN"


def test_event_score_is_descriptive_only():
    skill = build_event_registry().get("EVENT.SCORE")
    for score in ("0", "3", "5", "9"):
        run_skill(skill, context_from_event_score(Decimal(score)))
