"""Phase 20.3a — the REGIME classification seam mirrors the regime engine.

Parity is exact by construction (the skill calls ``classify_regime``), asserted
end-to-end across varied inputs: the SkillResult carries the regime state in
``label``, the engine risk level, prose, watchpoints, and a per-state audit id.
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.regime.regime_engine import RegimeInput, classify_regime
from finskillos.skills.regime_registry import (
    build_regime_registry,
    context_from_regime_input,
)

_CASES = [
    # Too few inputs → UNKNOWN.
    RegimeInput(
        spy_trend_state=None,
        qqq_trend_state=None,
        smh_trend_state=None,
        spy_rsi_14=None,
        qqq_rsi_14=None,
        smh_rsi_14=None,
        vix_close=None,
        dxy_trend_state=None,
        us10y_trend_state=None,
    ),
    # Broadly constructive.
    RegimeInput(
        spy_trend_state="BULLISH",
        qqq_trend_state="BULLISH",
        smh_trend_state="WEAK_BULLISH",
        spy_rsi_14=Decimal("58"),
        qqq_rsi_14=Decimal("61"),
        smh_rsi_14=Decimal("55"),
        vix_close=Decimal("15"),
        dxy_trend_state="NEUTRAL",
        us10y_trend_state="NEUTRAL",
        breadth_score=Decimal("62"),
        momentum_score=Decimal("60"),
    ),
    # Stress / risk-off.
    RegimeInput(
        spy_trend_state="BEARISH",
        qqq_trend_state="BEARISH",
        smh_trend_state="BEARISH",
        spy_rsi_14=Decimal("28"),
        qqq_rsi_14=Decimal("25"),
        smh_rsi_14=Decimal("22"),
        vix_close=Decimal("38"),
        dxy_trend_state="BULLISH",
        us10y_trend_state="BULLISH",
        breadth_score=Decimal("18"),
        momentum_score=Decimal("20"),
    ),
]


def test_regime_seam_mirrors_classify_regime():
    registry = build_regime_registry()
    for regime_input in _CASES:
        output = classify_regime(regime_input)
        (result,), (record,) = registry.run_all(
            context_from_regime_input(regime_input)
        )
        assert result.skill_id == "REGIME.CLASSIFY"
        assert result.label == output.regime
        assert result.risk_level == output.risk_level
        assert result.title == output.summary
        assert result.message == output.what_happened
        assert result.watch_next == tuple(output.watch_next)
        assert result.version == output.rule_version
        assert result.fired_rule_ids == (output.classification_rule_id,)
        assert result.fired_rule_ids[0].startswith("REGIME.CLASSIFY-")
        assert result.evidence["decision_mode"] == output.decision_mode
        assert result.evidence["confidence"] == output.confidence
        # Audit row stays aligned.
        assert record.skill_id == "REGIME.CLASSIFY"
        assert record.fired_rule_ids == result.fired_rule_ids
        assert record.status == "INFO"


def test_regime_seam_is_descriptive_only():
    # The runner safety scan must not raise for any case (regime prose is
    # descriptive by the engine's own FORBIDDEN_WORDS contract).
    registry = build_regime_registry()
    for regime_input in _CASES:
        registry.run_all(context_from_regime_input(regime_input))


def test_classification_rule_ids_are_recorded():
    from finskillos.regime.regime_engine import (
        RULE_INSUFFICIENT_INPUTS,
        classify_regime,
    )

    # Too few inputs → the insufficient-inputs rule id (before the ladder).
    assert classify_regime(_CASES[0]).classification_rule_id == (
        RULE_INSUFFICIENT_INPUTS
    )
    # Populated cases get a ladder rule id.
    for regime_input in _CASES[1:]:
        out = classify_regime(regime_input)
        assert out.classification_rule_id.startswith("REGIME.CLASSIFY-")
        assert out.classification_rule_id != RULE_INSUFFICIENT_INPUTS


def test_classification_table_is_ordered_and_unique():
    from finskillos.regime.regime_engine import CLASSIFICATION_RULES

    ids = [rule_id for rule_id, _pred, _state in CLASSIFICATION_RULES]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_classify_state_with_rule_matches_classify_regime():
    from finskillos.regime.regime_engine import (
        _compute_scores,
        classify_regime,
        classify_state_with_rule,
    )

    # The table walk agrees with the engine's recorded rule id on populated input.
    for regime_input in _CASES[1:]:
        state, rule_id = classify_state_with_rule(
            regime_input, _compute_scores(regime_input)
        )
        out = classify_regime(regime_input)
        assert state == out.regime
        assert rule_id == out.classification_rule_id
