"""Slice 06 — pure Risk Guard tests.

Drives every guard with deterministic fixtures across PASS / WARN /
FAIL boundaries. Also enforces SAFE-AC-001 over every guard's title,
message, and watch_next strings — no buy/sell wording can reach the
Risk Firewall.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from finskillos.guards import (
    GUARD_CASH_RATIO,
    GUARD_DRAWDOWN,
    GUARD_EVENT_PLACEHOLDER,
    GUARD_GOAL_PROTECTION,
    GUARD_OVERHEAT_ENTRY,
    GUARD_REGIME_RISK,
    GUARD_SECTOR_CONCENTRATION,
    GUARD_SINGLE_POSITION,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
    GuardInput,
    GuardResult,
    PositionRiskInput,
    assert_no_forbidden_wording,
    cash_ratio_guard,
    concentration_guard,
    drawdown_guard,
    event_risk_guard,
    goal_guard,
    overheat_guard,
    regime_guard,
    risk_level_to_severity,
    single_position_guard,
    worst_risk_level,
    worst_status,
)
from finskillos.regime.regime_rules import FORBIDDEN_WORDS

ACC = uuid.UUID("00000000-0000-4000-8000-000000000001")


def _base_input(**overrides: object) -> GuardInput:
    defaults: dict = {
        "account_id": ACC,
        "total_value": Decimal("57000000"),
        "cash_value": Decimal("10000000"),
        "target_value": Decimal("100000000"),
        "peak_value": Decimal("57000000"),
        "drawdown_pct": Decimal("0"),
        "positions": (
            PositionRiskInput("SPY", Decimal("9000000"), "Index"),
        ),
        "regime": "HEALTHY_BULL",
        "regime_risk_level": RISK_GREEN,
        "decision_mode": "SELECTIVE_ATTACK",
        "goal_progress_pct": Decimal("57"),
    }
    defaults.update(overrides)
    return GuardInput(**defaults)  # type: ignore[arg-type]


def _check_safety(result: GuardResult) -> None:
    # Should never raise.
    assert_no_forbidden_wording(result)


# ---------------------------------------------------------------------------
# Cash Ratio Guard
# ---------------------------------------------------------------------------


def test_cash_ratio_pass_when_above_minimum() -> None:
    result = cash_ratio_guard.evaluate(
        _base_input(
            total_value=Decimal("57000000"), cash_value=Decimal("10000000")
        )
    )
    assert result.guard_name == GUARD_CASH_RATIO
    assert result.status == STATUS_PASS
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


def test_cash_ratio_warn_when_between_fail_and_min() -> None:
    result = cash_ratio_guard.evaluate(
        _base_input(
            total_value=Decimal("100000000"),
            cash_value=Decimal("7000000"),
        )
    )
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_cash_ratio_fail_when_below_safety_floor() -> None:
    result = cash_ratio_guard.evaluate(
        _base_input(
            total_value=Decimal("100000000"),
            cash_value=Decimal("3000000"),
        )
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    _check_safety(result)


def test_cash_ratio_info_when_total_value_zero() -> None:
    result = cash_ratio_guard.evaluate(
        _base_input(
            total_value=Decimal("0"),
            cash_value=Decimal("0"),
            positions=(),
        )
    )
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_UNKNOWN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Single Position Limit Guard
# ---------------------------------------------------------------------------


def test_single_position_pass_when_all_below_limit() -> None:
    result = single_position_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("SPY", Decimal("5000000")),
                PositionRiskInput("QQQ", Decimal("8000000")),
            )
        )
    )
    assert result.status == STATUS_PASS
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


def test_single_position_warn_when_approaching_limit() -> None:
    result = single_position_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("TSLA", Decimal("9500000")),
            )
        )
    )
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_single_position_fail_when_over_limit() -> None:
    result = single_position_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("TSLA", Decimal("11000000")),
            )
        )
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    assert "TSLA" in result.message
    _check_safety(result)


def test_single_position_limit_is_configurable() -> None:
    """User policy is 10M KRW but the limit must be overridable."""

    result = single_position_guard.evaluate(
        _base_input(
            single_position_limit=Decimal("5000000"),
            positions=(
                PositionRiskInput("TSLA", Decimal("6000000")),
            ),
        )
    )
    assert result.status == STATUS_FAIL
    _check_safety(result)


# ---------------------------------------------------------------------------
# Sector Concentration Guard
# ---------------------------------------------------------------------------


def test_sector_concentration_pass_when_well_distributed() -> None:
    result = concentration_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("SPY", Decimal("4000000"), "Index"),
                PositionRiskInput("QQQ", Decimal("4000000"), "Tech"),
                PositionRiskInput("ARKX", Decimal("4000000"), "Space"),
                PositionRiskInput("PAVE", Decimal("4000000"), "Infra"),
            )
        )
    )
    assert result.status == STATUS_PASS
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


def test_sector_concentration_warn_when_share_above_35pct() -> None:
    result = concentration_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("NVDA", Decimal("4000000"), "Semiconductors"),
                PositionRiskInput("AMD", Decimal("1000000"), "Semiconductors"),
                PositionRiskInput("AAPL", Decimal("3000000"), "Mega Cap Tech"),
                PositionRiskInput("SPY", Decimal("3000000"), "Index"),
            )
        )
    )
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_sector_concentration_fail_when_over_50pct() -> None:
    result = concentration_guard.evaluate(
        _base_input(
            positions=(
                PositionRiskInput("NVDA", Decimal("8000000"), "Semiconductors"),
                PositionRiskInput("AMD", Decimal("3000000"), "Semiconductors"),
                PositionRiskInput("SPY", Decimal("2000000"), "Index"),
            )
        )
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    assert "Semiconductors" in result.message
    _check_safety(result)


def test_sector_concentration_info_when_no_positions() -> None:
    result = concentration_guard.evaluate(_base_input(positions=()))
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_UNKNOWN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Drawdown Guard
# ---------------------------------------------------------------------------


def test_drawdown_pass_in_normal_band() -> None:
    result = drawdown_guard.evaluate(
        _base_input(drawdown_pct=Decimal("-3.5"))
    )
    assert result.status == STATUS_PASS
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


def test_drawdown_warn_in_yellow_band() -> None:
    result = drawdown_guard.evaluate(
        _base_input(drawdown_pct=Decimal("-8.87"))
    )
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_drawdown_fail_orange_band() -> None:
    result = drawdown_guard.evaluate(
        _base_input(drawdown_pct=Decimal("-12"))
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    _check_safety(result)


def test_drawdown_fail_red_band() -> None:
    result = drawdown_guard.evaluate(
        _base_input(drawdown_pct=Decimal("-18"))
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_RED
    _check_safety(result)


def test_drawdown_info_when_no_peak_data() -> None:
    result = drawdown_guard.evaluate(
        _base_input(peak_value=None, drawdown_pct=None)
    )
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_UNKNOWN
    _check_safety(result)


def test_drawdown_derives_from_peak_when_pct_missing() -> None:
    result = drawdown_guard.evaluate(
        _base_input(
            peak_value=Decimal("62000000"),
            total_value=Decimal("56500000"),
            drawdown_pct=None,
        )
    )
    # 56.5/62 -> -8.87% → WARN
    assert result.status == STATUS_WARN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Goal Protection Guard
# ---------------------------------------------------------------------------


def test_goal_protection_pass_below_70pct() -> None:
    result = goal_guard.evaluate(_base_input(goal_progress_pct=Decimal("57")))
    assert result.status == STATUS_PASS
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


def test_goal_protection_warn_in_balanced_band() -> None:
    result = goal_guard.evaluate(_base_input(goal_progress_pct=Decimal("75")))
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_goal_protection_fail_in_protection_band() -> None:
    result = goal_guard.evaluate(_base_input(goal_progress_pct=Decimal("92")))
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    _check_safety(result)


def test_goal_protection_blocked_at_or_above_100pct() -> None:
    result = goal_guard.evaluate(
        _base_input(goal_progress_pct=Decimal("100"))
    )
    assert result.status == STATUS_BLOCKED
    assert result.risk_level == RISK_RED
    # Even the early-stop wording must be free of "sell everything".
    _check_safety(result)


def test_goal_protection_info_when_progress_unknown() -> None:
    result = goal_guard.evaluate(_base_input(goal_progress_pct=None))
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_UNKNOWN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Regime Risk Guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "regime,risk_level,expected_status",
    [
        ("HEALTHY_BULL", RISK_GREEN, STATUS_PASS),
        ("RISK_ON_OVERHEAT", RISK_YELLOW, STATUS_WARN),
        ("DISTRIBUTION_RISK", RISK_ORANGE, STATUS_FAIL),
        ("RISK_OFF", RISK_RED, STATUS_FAIL),
    ],
)
def test_regime_guard_maps_risk_level_to_status(
    regime: str, risk_level: str, expected_status: str
) -> None:
    result = regime_guard.evaluate(
        _base_input(
            regime=regime,
            regime_risk_level=risk_level,
            decision_mode="SELECTIVE_ATTACK",
        )
    )
    assert result.status == expected_status
    assert result.guard_name == GUARD_REGIME_RISK
    _check_safety(result)


def test_regime_guard_info_when_regime_missing() -> None:
    result = regime_guard.evaluate(
        _base_input(
            regime=None,
            regime_risk_level=None,
            decision_mode=None,
        )
    )
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_UNKNOWN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Overheat Entry Guard
# ---------------------------------------------------------------------------


def test_overheat_guard_fires_on_risk_on_overheat() -> None:
    result = overheat_guard.evaluate(
        _base_input(regime="RISK_ON_OVERHEAT")
    )
    assert result.status == STATUS_FAIL
    assert result.risk_level == RISK_ORANGE
    assert result.guard_name == GUARD_OVERHEAT_ENTRY
    _check_safety(result)


def test_overheat_guard_warns_on_distribution_risk() -> None:
    result = overheat_guard.evaluate(
        _base_input(regime="DISTRIBUTION_RISK")
    )
    assert result.status == STATUS_WARN
    assert result.risk_level == RISK_YELLOW
    _check_safety(result)


def test_overheat_guard_pass_otherwise() -> None:
    result = overheat_guard.evaluate(_base_input(regime="HEALTHY_BULL"))
    assert result.status == STATUS_PASS
    _check_safety(result)


def test_overheat_guard_info_when_regime_missing() -> None:
    result = overheat_guard.evaluate(_base_input(regime=None))
    assert result.status == STATUS_INFO
    _check_safety(result)


# ---------------------------------------------------------------------------
# Event Risk Guard (placeholder)
# ---------------------------------------------------------------------------


def test_event_risk_guard_is_informational_placeholder() -> None:
    result = event_risk_guard.evaluate(_base_input())
    assert result.guard_name == GUARD_EVENT_PLACEHOLDER
    assert result.status == STATUS_INFO
    assert result.risk_level == RISK_GREEN
    _check_safety(result)


# ---------------------------------------------------------------------------
# Empty / edge-case portfolio
# ---------------------------------------------------------------------------


def test_empty_portfolio_does_not_crash_any_guard() -> None:
    inputs = _base_input(
        total_value=Decimal("0"),
        cash_value=Decimal("0"),
        peak_value=None,
        drawdown_pct=None,
        positions=(),
        regime=None,
        regime_risk_level=None,
        decision_mode=None,
        goal_progress_pct=None,
    )
    for evaluator in (
        cash_ratio_guard.evaluate,
        single_position_guard.evaluate,
        concentration_guard.evaluate,
        drawdown_guard.evaluate,
        goal_guard.evaluate,
        regime_guard.evaluate,
        overheat_guard.evaluate,
        event_risk_guard.evaluate,
    ):
        result = evaluator(inputs)
        assert isinstance(result, GuardResult)
        _check_safety(result)


# ---------------------------------------------------------------------------
# Forbidden wording check (parametric, covers every guard branch)
# ---------------------------------------------------------------------------


_SAFETY_CASES = [
    _base_input(),  # neutral
    _base_input(  # extreme drawdown
        drawdown_pct=Decimal("-22"),
        regime="PANIC",
        regime_risk_level=RISK_RED,
        decision_mode="PROTECTION_MODE",
    ),
    _base_input(  # overheat
        regime="RISK_ON_OVERHEAT",
        regime_risk_level=RISK_YELLOW,
        decision_mode="HOLD_WINNERS",
        positions=(PositionRiskInput("TSLA", Decimal("11500000"), "EV"),),
    ),
    _base_input(  # goal complete
        goal_progress_pct=Decimal("105"),
    ),
]


@pytest.mark.parametrize("inputs", _SAFETY_CASES)
def test_every_guard_output_avoids_forbidden_wording(inputs: GuardInput) -> None:
    evaluators = (
        cash_ratio_guard.evaluate,
        single_position_guard.evaluate,
        concentration_guard.evaluate,
        drawdown_guard.evaluate,
        goal_guard.evaluate,
        regime_guard.evaluate,
        overheat_guard.evaluate,
        event_risk_guard.evaluate,
    )
    for evaluator in evaluators:
        result = evaluator(inputs)
        blob = " ".join([result.title, result.message, *result.watch_next])
        for forbidden in FORBIDDEN_WORDS:
            assert forbidden not in blob, (
                f"{result.guard_name} leaked {forbidden!r}: {blob!r}"
            )


# ---------------------------------------------------------------------------
# Helpers / shared utilities
# ---------------------------------------------------------------------------


def test_worst_status_picks_blocked_over_fail_over_warn() -> None:
    assert worst_status(()) == STATUS_PASS
    assert worst_status((STATUS_PASS, STATUS_WARN)) == STATUS_WARN
    assert worst_status((STATUS_WARN, STATUS_FAIL)) == STATUS_FAIL
    assert worst_status((STATUS_FAIL, STATUS_BLOCKED)) == STATUS_BLOCKED


def test_worst_risk_level_picks_red_over_orange_over_yellow() -> None:
    assert worst_risk_level(()) == RISK_GREEN
    assert worst_risk_level((RISK_GREEN, RISK_YELLOW)) == RISK_YELLOW
    assert worst_risk_level((RISK_YELLOW, RISK_ORANGE)) == RISK_ORANGE
    assert worst_risk_level((RISK_ORANGE, RISK_RED)) == RISK_RED


def test_risk_level_to_severity_maps_alert_vocabulary() -> None:
    assert risk_level_to_severity(RISK_RED) == "RED"
    assert risk_level_to_severity(RISK_ORANGE) == "ORANGE"
    assert risk_level_to_severity(RISK_YELLOW) == "YELLOW"
    assert risk_level_to_severity(RISK_GREEN) == "INFO"
    assert risk_level_to_severity(RISK_UNKNOWN) == "INFO"


def test_guards_module_exports_canonical_names() -> None:
    from finskillos.guards import ALL_GUARDS

    assert set(ALL_GUARDS) == {
        GUARD_CASH_RATIO,
        GUARD_SINGLE_POSITION,
        GUARD_SECTOR_CONCENTRATION,
        GUARD_DRAWDOWN,
        GUARD_GOAL_PROTECTION,
        GUARD_REGIME_RISK,
        GUARD_OVERHEAT_ENTRY,
        GUARD_EVENT_PLACEHOLDER,
    }


# ---------------------------------------------------------------------------
# Safety checker hardening (06 cleanup)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "Sell TSLA now.",
        "sell TSLA now.",
        "BUY NVDA.",
        "buy NVDA.",
        "지금 사라.",
        "지금 팔아라.",
        "이 종목은 무조건 수익 보장입니다.",
        "원금 보장입니다.",
        "This is guaranteed profit.",
        "반드시 진입하세요.",
    ],
)
def test_forbidden_wording_check_blocks_direct_advice_case_insensitively(
    message: str,
) -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_WARN,
        risk_level=RISK_YELLOW,
        title="Safety check",
        message=message,
    )
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(result)


def test_forbidden_wording_check_allows_sell_the_news_idiom() -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="Event reaction risk",
        message=(
            "The system will track sell-the-news risk once event data is connected."
        ),
    )
    # Must not raise.
    assert_no_forbidden_wording(result)


def test_forbidden_wording_check_allows_capitalised_sell_the_news_idiom() -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="Sell-the-news pattern",
        message="Sell-the-news reactions can appear after a strong earnings beat.",
    )
    assert_no_forbidden_wording(result)


def test_forbidden_wording_check_allows_oversold_word_boundary() -> None:
    """The hardened checker uses \\bSELL\\b — words containing 'sell' must pass."""

    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="RSI 30 이하의 oversold 구간 관찰",
        message="oversold reading is descriptive, not a transaction directive.",
    )
    assert_no_forbidden_wording(result)


def test_forbidden_wording_check_scans_watch_next_and_evidence_strings() -> None:
    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_WARN,
        risk_level=RISK_YELLOW,
        title="ok",
        message="ok",
        watch_next=("sell now",),
    )
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(result)

    result = GuardResult(
        guard_name="TEST_GUARD",
        status=STATUS_WARN,
        risk_level=RISK_YELLOW,
        title="ok",
        message="ok",
        evidence={"recommendation": "지금 사라"},
    )
    with pytest.raises(AssertionError):
        assert_no_forbidden_wording(result)


def test_event_placeholder_guard_sell_the_news_idiom_is_allowed() -> None:
    """Real Event Risk Guard output must still pass the hardened checker."""

    result = event_risk_guard.evaluate(_base_input())
    assert_no_forbidden_wording(result)
