"""Declarative conditions for strategy specs (Phase 21).

A condition is a small, composable, JSON-serialisable predicate over per-bar
features (the same vocabulary the skills use: close, sma_N, rsi_14, trend, regime,
drawdown_pct, …). The agent composes these from natural language; the engine
evaluates them bar-by-bar. No buy/sell semantics live here — a condition only says
when simulated *exposure* turns ON or OFF.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

# feature name -> value (numeric features as float; categorical like regime as str)
FeatureRow = Mapping[str, float | str | None]

_NUMERIC_OPS = ("<", "<=", ">", ">=")


@dataclass(frozen=True)
class Compare:
    """``feature <op> value`` (== works for categorical features like regime)."""

    feature: str
    op: str
    value: float | str


@dataclass(frozen=True)
class Cross:
    """``feature`` crosses ``above`` / ``below`` ``reference`` (another feature)."""

    feature: str
    direction: str  # "above" | "below"
    reference: str


@dataclass(frozen=True)
class All:
    terms: tuple[Condition, ...]


@dataclass(frozen=True)
class Any:
    terms: tuple[Condition, ...]


Condition = Compare | Cross | All | Any


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _compare(cur: FeatureRow, cond: Compare) -> bool:
    left = cur.get(cond.feature)
    if cond.op == "==":
        return left == cond.value
    lf, rf = _as_float(left), _as_float(cond.value)
    if lf is None or rf is None:
        return False
    if cond.op == "<":
        return lf < rf
    if cond.op == "<=":
        return lf <= rf
    if cond.op == ">":
        return lf > rf
    if cond.op == ">=":
        return lf >= rf
    return False


def _cross(cur: FeatureRow, prev: FeatureRow | None, cond: Cross) -> bool:
    if prev is None:
        return False
    a0, b0 = _as_float(prev.get(cond.feature)), _as_float(prev.get(cond.reference))
    a1, b1 = _as_float(cur.get(cond.feature)), _as_float(cur.get(cond.reference))
    if None in (a0, b0, a1, b1):
        return False
    if cond.direction == "above":
        return a0 <= b0 and a1 > b1
    if cond.direction == "below":
        return a0 >= b0 and a1 < b1
    return False


def evaluate(cond: Condition, cur: FeatureRow, prev: FeatureRow | None) -> bool:
    """True when the condition holds for the current bar (``prev`` for crosses)."""

    if isinstance(cond, Compare):
        return _compare(cur, cond)
    if isinstance(cond, Cross):
        return _cross(cur, prev, cond)
    if isinstance(cond, All):
        return all(evaluate(t, cur, prev) for t in cond.terms)
    if isinstance(cond, Any):
        return any(evaluate(t, cur, prev) for t in cond.terms)
    return False


def referenced_features(cond: Condition) -> set[str]:
    """All feature names the condition reads — lets the engine compute only what's
    needed (e.g. which sma_N windows)."""

    if isinstance(cond, Compare):
        names = {cond.feature}
        if isinstance(cond.value, str):
            names.add(cond.value)
        return names
    if isinstance(cond, Cross):
        return {cond.feature, cond.reference}
    if isinstance(cond, (All, Any)):
        out: set[str] = set()
        for term in cond.terms:
            out |= referenced_features(term)
        return out
    return set()
