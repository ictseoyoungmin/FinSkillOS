"""Static rule constants for the Slice-05 Market Regime Engine.

Holds the regime / decision-mode / risk-level vocabularies plus the
numeric thresholds that the pure rule engine consults. Lives in its
own module so the engine stays focused on classification and so the
rulebook can be tuned (docs/v2_1/06 §15: rule_version bookkeeping)
without touching application logic.

Nothing in this module emits trading directives. Decision modes are
descriptive operating postures, never "buy" / "sell".
"""

from __future__ import annotations

from decimal import Decimal
from typing import Final

RULE_VERSION: Final[str] = "regime-v1-2026-05-18"

# --- Regime states (docs/v2_1/06 §3 + .devmd/05) -------------------------
REGIME_PANIC: Final[str] = "PANIC"
REGIME_RECOVERY: Final[str] = "RECOVERY"
REGIME_HEALTHY_BULL: Final[str] = "HEALTHY_BULL"
REGIME_AGGRESSIVE_RISK_ON: Final[str] = "AGGRESSIVE_RISK_ON"
REGIME_RISK_ON_OVERHEAT: Final[str] = "RISK_ON_OVERHEAT"
REGIME_DISTRIBUTION_RISK: Final[str] = "DISTRIBUTION_RISK"
REGIME_DEFENSIVE_TRANSITION: Final[str] = "DEFENSIVE_TRANSITION"
REGIME_RISK_OFF: Final[str] = "RISK_OFF"
REGIME_UNKNOWN: Final[str] = "UNKNOWN"

REGIMES: Final[tuple[str, ...]] = (
    REGIME_PANIC,
    REGIME_RECOVERY,
    REGIME_HEALTHY_BULL,
    REGIME_AGGRESSIVE_RISK_ON,
    REGIME_RISK_ON_OVERHEAT,
    REGIME_DISTRIBUTION_RISK,
    REGIME_DEFENSIVE_TRANSITION,
    REGIME_RISK_OFF,
    REGIME_UNKNOWN,
)

# --- Decision modes -------------------------------------------------------
MODE_DEFENSIVE: Final[str] = "DEFENSIVE"
MODE_CAUTIOUS_RECOVERY: Final[str] = "CAUTIOUS_RECOVERY"
MODE_SELECTIVE_ATTACK: Final[str] = "SELECTIVE_ATTACK"
MODE_HOLD_WINNERS: Final[str] = "HOLD_WINNERS"
MODE_LIMIT_NEW_ENTRIES: Final[str] = "LIMIT_NEW_ENTRIES"
MODE_PROTECTION: Final[str] = "PROTECTION_MODE"
MODE_REVIEW_ONLY: Final[str] = "REVIEW_ONLY"
MODE_UNKNOWN: Final[str] = "UNKNOWN"

DECISION_MODES: Final[tuple[str, ...]] = (
    MODE_DEFENSIVE,
    MODE_CAUTIOUS_RECOVERY,
    MODE_SELECTIVE_ATTACK,
    MODE_HOLD_WINNERS,
    MODE_LIMIT_NEW_ENTRIES,
    MODE_PROTECTION,
    MODE_REVIEW_ONLY,
    MODE_UNKNOWN,
)

# --- Risk levels ----------------------------------------------------------
RISK_GREEN: Final[str] = "GREEN"
RISK_YELLOW: Final[str] = "YELLOW"
RISK_ORANGE: Final[str] = "ORANGE"
RISK_RED: Final[str] = "RED"
RISK_UNKNOWN: Final[str] = "UNKNOWN"

# --- Trend-state labels emitted by signals.technical.trend_state ----------
TREND_BULLISH: Final[str] = "BULLISH"
TREND_WEAK_BULLISH: Final[str] = "WEAK_BULLISH"
TREND_NEUTRAL: Final[str] = "NEUTRAL"
TREND_WEAK_BEARISH: Final[str] = "WEAK_BEARISH"
TREND_BEARISH: Final[str] = "BEARISH"

BULLISH_TRENDS: Final[frozenset[str]] = frozenset(
    {TREND_BULLISH, TREND_WEAK_BULLISH}
)
BEARISH_TRENDS: Final[frozenset[str]] = frozenset(
    {TREND_BEARISH, TREND_WEAK_BEARISH}
)

# --- Numeric thresholds (docs/v2_1/06 §4) ---------------------------------
VIX_PANIC: Final[Decimal] = Decimal("30")
VIX_RISK_OFF: Final[Decimal] = Decimal("25")
VIX_CAUTION: Final[Decimal] = Decimal("20")
VIX_CALM: Final[Decimal] = Decimal("15")

RSI_OVERSOLD: Final[Decimal] = Decimal("30")
RSI_RECOVERY_LOW: Final[Decimal] = Decimal("40")
RSI_RECOVERY_HIGH: Final[Decimal] = Decimal("55")
RSI_HEALTHY_LOW: Final[Decimal] = Decimal("50")
RSI_HEALTHY_HIGH: Final[Decimal] = Decimal("68")
RSI_AGGRESSIVE_LOW: Final[Decimal] = Decimal("60")
RSI_AGGRESSIVE_HIGH: Final[Decimal] = Decimal("75")
RSI_OVERHEAT: Final[Decimal] = Decimal("70")

CONFIDENCE_FULL: Final[Decimal] = Decimal("100")
CONFIDENCE_PER_MISSING_INPUT: Final[Decimal] = Decimal("8")
CONFIDENCE_PER_CONFLICT: Final[Decimal] = Decimal("12")
CONFIDENCE_FLOOR: Final[Decimal] = Decimal("0")
CONFIDENCE_LOW_THRESHOLD: Final[Decimal] = Decimal("40")

# --- Forbidden wording (SAFE-AC-001) --------------------------------------
FORBIDDEN_WORDS: Final[tuple[str, ...]] = (
    "BUY",
    "SELL",
    "매수",
    "매도",
    "무조건",
    "확실",
    "수익 보장",
    "guaranteed",
    "지금 사라",
    "지금 팔아라",
    "원금 보장",
    "반드시",
)


def regime_to_mode(regime: str) -> str:
    """Map a regime label to its descriptive operating mode."""
    return {
        REGIME_PANIC: MODE_PROTECTION,
        REGIME_RISK_OFF: MODE_DEFENSIVE,
        REGIME_DEFENSIVE_TRANSITION: MODE_LIMIT_NEW_ENTRIES,
        REGIME_DISTRIBUTION_RISK: MODE_LIMIT_NEW_ENTRIES,
        REGIME_RECOVERY: MODE_CAUTIOUS_RECOVERY,
        REGIME_HEALTHY_BULL: MODE_SELECTIVE_ATTACK,
        REGIME_AGGRESSIVE_RISK_ON: MODE_SELECTIVE_ATTACK,
        REGIME_RISK_ON_OVERHEAT: MODE_HOLD_WINNERS,
        REGIME_UNKNOWN: MODE_REVIEW_ONLY,
    }.get(regime, MODE_REVIEW_ONLY)


def regime_to_risk_level(regime: str) -> str:
    """Map a regime label to a descriptive RAG / risk colour."""
    return {
        REGIME_PANIC: RISK_RED,
        REGIME_RISK_OFF: RISK_RED,
        REGIME_DEFENSIVE_TRANSITION: RISK_ORANGE,
        REGIME_DISTRIBUTION_RISK: RISK_ORANGE,
        REGIME_RECOVERY: RISK_YELLOW,
        REGIME_RISK_ON_OVERHEAT: RISK_YELLOW,
        REGIME_AGGRESSIVE_RISK_ON: RISK_YELLOW,
        REGIME_HEALTHY_BULL: RISK_GREEN,
        REGIME_UNKNOWN: RISK_UNKNOWN,
    }.get(regime, RISK_UNKNOWN)
