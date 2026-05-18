"""Slice 05 — pure Market Regime Engine tests.

Covers every regime branch with a deterministic fixture so the rule
ladder stays inspectable (.devmd/05 acceptance: each regime reachable
from a fixed input). Also enforces:

* confidence is bounded in [0, 100]
* every interpretation field is free of buy/sell wording (SAFE-AC-001)
* missing / sparse inputs return UNKNOWN with zero confidence
* the conflict case (overheat + strong trend) maps to RISK_ON_OVERHEAT,
  not a bearish reversal — docs/v2_1/06 §7 / REG-AC-004.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from finskillos.regime import (
    FORBIDDEN_WORDS,
    REGIMES,
    RegimeInput,
    RegimeOutput,
    classify_regime,
)
from finskillos.regime.regime_rules import (
    MODE_CAUTIOUS_RECOVERY,
    MODE_DEFENSIVE,
    MODE_HOLD_WINNERS,
    MODE_LIMIT_NEW_ENTRIES,
    MODE_PROTECTION,
    MODE_REVIEW_ONLY,
    MODE_SELECTIVE_ATTACK,
    REGIME_AGGRESSIVE_RISK_ON,
    REGIME_DEFENSIVE_TRANSITION,
    REGIME_DISTRIBUTION_RISK,
    REGIME_HEALTHY_BULL,
    REGIME_PANIC,
    REGIME_RECOVERY,
    REGIME_RISK_OFF,
    REGIME_RISK_ON_OVERHEAT,
    REGIME_UNKNOWN,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _input(**overrides: object) -> RegimeInput:
    """Build a RegimeInput with sensible defaults; overrides win."""
    base: dict = {
        "spy_trend_state": "NEUTRAL",
        "qqq_trend_state": "NEUTRAL",
        "smh_trend_state": "NEUTRAL",
        "spy_rsi_14": Decimal("50"),
        "qqq_rsi_14": Decimal("50"),
        "smh_rsi_14": Decimal("50"),
        "vix_close": Decimal("16"),
        "dxy_trend_state": "NEUTRAL",
        "us10y_trend_state": "NEUTRAL",
    }
    base.update(overrides)
    return RegimeInput(**base)  # type: ignore[arg-type]


def _assert_no_forbidden_wording(output: RegimeOutput) -> None:
    strings = [
        output.regime,
        output.decision_mode,
        output.risk_level,
        output.summary,
        output.what_happened,
        output.what_it_means,
        *output.watch_next,
    ]
    blob = " ".join(strings)
    for forbidden in FORBIDDEN_WORDS:
        assert forbidden not in blob, (
            f"forbidden term {forbidden!r} appears in regime output: {blob!r}"
        )


# ---------------------------------------------------------------------------
# Regime branches
# ---------------------------------------------------------------------------


def test_panic_when_vix_extreme_and_indices_bearish() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BEARISH",
            qqq_trend_state="BEARISH",
            smh_trend_state="BEARISH",
            spy_rsi_14=Decimal("22"),
            qqq_rsi_14=Decimal("20"),
            smh_rsi_14=Decimal("18"),
            vix_close=Decimal("38"),
            dxy_trend_state="BULLISH",
            us10y_trend_state="BULLISH",
        )
    )
    assert output.regime == REGIME_PANIC
    assert output.decision_mode == MODE_PROTECTION
    assert output.risk_level == RISK_RED
    _assert_no_forbidden_wording(output)


def test_risk_off_when_vix_high_and_trend_bearish() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BEARISH",
            qqq_trend_state="WEAK_BEARISH",
            smh_trend_state="BEARISH",
            spy_rsi_14=Decimal("35"),
            qqq_rsi_14=Decimal("38"),
            smh_rsi_14=Decimal("35"),
            vix_close=Decimal("28"),
            dxy_trend_state="BULLISH",
            us10y_trend_state="BULLISH",
        )
    )
    assert output.regime == REGIME_RISK_OFF
    assert output.decision_mode == MODE_DEFENSIVE
    assert output.risk_level == RISK_RED
    _assert_no_forbidden_wording(output)


def test_defensive_transition_when_vix_caution_and_trend_weakening() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="NEUTRAL",
            qqq_trend_state="WEAK_BEARISH",
            smh_trend_state="WEAK_BEARISH",
            spy_rsi_14=Decimal("45"),
            qqq_rsi_14=Decimal("42"),
            smh_rsi_14=Decimal("40"),
            vix_close=Decimal("22"),
            dxy_trend_state="BULLISH",
            us10y_trend_state="BULLISH",
        )
    )
    assert output.regime == REGIME_DEFENSIVE_TRANSITION
    assert output.decision_mode == MODE_LIMIT_NEW_ENTRIES
    assert output.risk_level == RISK_ORANGE
    _assert_no_forbidden_wording(output)


def test_recovery_when_vix_cool_and_rsi_rebuilds() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="NEUTRAL",
            qqq_trend_state="WEAK_BULLISH",
            smh_trend_state="NEUTRAL",
            spy_rsi_14=Decimal("48"),
            qqq_rsi_14=Decimal("48"),
            smh_rsi_14=Decimal("45"),
            vix_close=Decimal("19"),
            dxy_trend_state="NEUTRAL",
            us10y_trend_state="NEUTRAL",
        )
    )
    assert output.regime == REGIME_RECOVERY
    assert output.decision_mode == MODE_CAUTIOUS_RECOVERY
    assert output.risk_level == RISK_YELLOW
    _assert_no_forbidden_wording(output)


def test_healthy_bull_when_stack_bullish_and_rsi_in_band() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="WEAK_BULLISH",
            spy_rsi_14=Decimal("58"),
            qqq_rsi_14=Decimal("60"),
            smh_rsi_14=Decimal("55"),
            vix_close=Decimal("14"),
        )
    )
    assert output.regime == REGIME_HEALTHY_BULL
    assert output.decision_mode == MODE_SELECTIVE_ATTACK
    assert output.risk_level == RISK_GREEN
    _assert_no_forbidden_wording(output)


def test_aggressive_risk_on_when_all_indices_strict_bullish_high_rsi() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("66"),
            qqq_rsi_14=Decimal("68"),
            smh_rsi_14=Decimal("70"),
            vix_close=Decimal("13"),
        )
    )
    assert output.regime == REGIME_AGGRESSIVE_RISK_ON
    assert output.decision_mode == MODE_SELECTIVE_ATTACK
    assert output.risk_level == RISK_YELLOW
    _assert_no_forbidden_wording(output)


def test_risk_on_overheat_when_trend_bullish_and_rsi_above_70() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("72"),
            qqq_rsi_14=Decimal("72"),
            smh_rsi_14=Decimal("78"),
            vix_close=Decimal("13.5"),
        )
    )
    assert output.regime == REGIME_RISK_ON_OVERHEAT
    assert output.decision_mode == MODE_HOLD_WINNERS
    assert output.risk_level == RISK_YELLOW
    _assert_no_forbidden_wording(output)


def test_distribution_risk_when_trend_bullish_but_momentum_negative() -> None:
    output = classify_regime(
        _input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="WEAK_BULLISH",
            spy_rsi_14=Decimal("60"),
            qqq_rsi_14=Decimal("62"),
            smh_rsi_14=Decimal("60"),
            vix_close=Decimal("16"),
            momentum_score=Decimal("-3"),
            breadth_score=Decimal("40"),
        )
    )
    assert output.regime == REGIME_DISTRIBUTION_RISK
    assert output.decision_mode == MODE_LIMIT_NEW_ENTRIES
    assert output.risk_level == RISK_ORANGE
    _assert_no_forbidden_wording(output)


# ---------------------------------------------------------------------------
# Conflict handling — RSI overheat + strong trend must not become bearish.
# ---------------------------------------------------------------------------


def test_conflict_overheat_with_strong_trend_resolves_to_overheat() -> None:
    """REG-AC-004 — RSI high, VIX low, sector momentum strong.

    The engine must NOT call this a bearish reversal. It must reach
    RISK_ON_OVERHEAT with a HOLD_WINNERS / LIMIT_NEW_ENTRIES style
    operating mode and explicitly avoid any sell wording.
    """

    output = classify_regime(
        _input(
            spy_trend_state="BULLISH",
            qqq_trend_state="BULLISH",
            smh_trend_state="BULLISH",
            spy_rsi_14=Decimal("70"),
            qqq_rsi_14=Decimal("75"),
            smh_rsi_14=Decimal("76"),
            vix_close=Decimal("13"),
            momentum_score=Decimal("18"),
        )
    )
    assert output.regime == REGIME_RISK_ON_OVERHEAT
    assert output.decision_mode == MODE_HOLD_WINNERS
    _assert_no_forbidden_wording(output)


# ---------------------------------------------------------------------------
# Missing data / safety / confidence bounds
# ---------------------------------------------------------------------------


def test_missing_inputs_return_unknown_with_zero_confidence() -> None:
    output = classify_regime(
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
        )
    )
    assert output.regime == REGIME_UNKNOWN
    assert output.decision_mode == MODE_REVIEW_ONLY
    assert output.risk_level == RISK_UNKNOWN
    assert output.confidence == Decimal("0")
    assert not output.is_actionable()
    _assert_no_forbidden_wording(output)


def test_sparse_inputs_yield_low_confidence_unknown() -> None:
    """Slightly more inputs than the UNKNOWN floor still must not invent a regime."""

    output = classify_regime(
        RegimeInput(
            spy_trend_state="NEUTRAL",
            qqq_trend_state=None,
            smh_trend_state=None,
            spy_rsi_14=Decimal("50"),
            qqq_rsi_14=None,
            smh_rsi_14=None,
            vix_close=None,
            dxy_trend_state=None,
            us10y_trend_state=None,
        )
    )
    assert output.regime == REGIME_UNKNOWN
    assert output.confidence == Decimal("0")


def test_confidence_is_bounded_between_0_and_100() -> None:
    cases = [
        _input(),
        _input(vix_close=Decimal("28"), spy_trend_state="BEARISH"),
        _input(qqq_rsi_14=Decimal("75"), smh_rsi_14=Decimal("78")),
    ]
    for inputs in cases:
        output = classify_regime(inputs)
        assert Decimal("0") <= output.confidence <= Decimal("100"), output


def test_output_evidence_carries_input_signals() -> None:
    inputs = _input(
        spy_trend_state="BULLISH",
        qqq_trend_state="BULLISH",
        vix_close=Decimal("17.25"),
        qqq_rsi_14=Decimal("64"),
    )
    output = classify_regime(inputs)
    assert output.evidence["spy_trend_state"] == "BULLISH"
    assert output.evidence["vix_close"] == Decimal("17.25")
    assert output.evidence["qqq_rsi_14"] == Decimal("64")
    # The four scores must always be exposed for drilldown.
    for key in (
        "risk_on_score",
        "overheat_score",
        "risk_off_score",
        "distribution_score",
    ):
        assert key in output.evidence


@pytest.mark.parametrize(
    "regime",
    [r for r in REGIMES if r != REGIME_UNKNOWN],
)
def test_every_regime_has_interpretation_block(regime: str) -> None:
    """Each non-UNKNOWN regime must ship complete interpretation text."""

    from finskillos.regime.regime_engine import (
        _WATCH_NEXT,
        _WHAT_HAPPENED,
        _WHAT_IT_MEANS,
    )

    assert _WHAT_HAPPENED[regime].strip()
    assert _WHAT_IT_MEANS[regime].strip()
    assert _WATCH_NEXT[regime]
    for watch in _WATCH_NEXT[regime]:
        for forbidden in FORBIDDEN_WORDS:
            assert forbidden not in watch
