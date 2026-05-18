"""Slice-05 Market Regime Engine.

Pure, rule-first translation of stored market indicators into a
descriptive market state, confidence score, decision mode, and
watchpoints. Nothing in this package emits buy/sell directives — it
explains what the market looks like and what to monitor next.
"""

from finskillos.regime.regime_engine import (
    RegimeInput,
    RegimeOutput,
    classify_regime,
)
from finskillos.regime.regime_rules import (
    DECISION_MODES,
    FORBIDDEN_WORDS,
    REGIMES,
    RULE_VERSION,
)

__all__ = [
    "DECISION_MODES",
    "FORBIDDEN_WORDS",
    "REGIMES",
    "RULE_VERSION",
    "RegimeInput",
    "RegimeOutput",
    "classify_regime",
]
