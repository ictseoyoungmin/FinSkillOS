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
        assert result.fired_rule_ids == (f"REGIME.CLASSIFY-{output.regime}",)
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
