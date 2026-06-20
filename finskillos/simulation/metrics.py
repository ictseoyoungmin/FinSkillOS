"""Descriptive performance / risk metrics for a simulated equity path (Phase 21).

Implements the legacy METRIC rulebook formulas (docs/v4/SKILL_RULEBOOK.md §1,
previously [ref]) over a daily-return series + its equity curve. These describe a
*given series'* risk-adjusted profile — not a recommendation. Computed in float
(deterministic; this is a simulation, not money accounting).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

_TRADING_DAYS = 252


@dataclass(frozen=True)
class SimMetrics:
    total_return: float
    cagr: float
    annual_volatility: float
    sharpe: float | None
    sortino: float | None
    max_drawdown: float
    calmar: float | None
    exposure_pct: float
    round_trips: int
    win_rate: float | None


def _std(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return math.sqrt(var)


def total_return(equity: Sequence[float]) -> float:
    if not equity:
        return 0.0
    return equity[-1] / equity[0] - 1.0


def cagr(equity: Sequence[float], periods: int) -> float:
    if not equity or equity[0] <= 0 or periods <= 0:
        return 0.0
    growth = equity[-1] / equity[0]
    if growth <= 0:
        return -1.0
    return growth ** (_TRADING_DAYS / periods) - 1.0


def annual_volatility(returns: Sequence[float]) -> float:
    return _std(returns) * math.sqrt(_TRADING_DAYS)


def sharpe(returns: Sequence[float]) -> float | None:
    vol = _std(returns)
    if vol == 0:
        return None
    mean = sum(returns) / len(returns)
    return (mean / vol) * math.sqrt(_TRADING_DAYS)


def sortino(returns: Sequence[float], target: float = 0.0) -> float | None:
    downside = [min(r - target, 0.0) for r in returns]
    dd = math.sqrt(sum(d * d for d in downside) / len(downside)) if downside else 0.0
    if dd == 0:
        return None
    mean = sum(returns) / len(returns)
    return ((mean - target) / dd) * math.sqrt(_TRADING_DAYS)


def max_drawdown(equity: Sequence[float]) -> float:
    peak = -math.inf
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def build_metrics(
    *,
    equity: Sequence[float],
    returns: Sequence[float],
    in_market_days: int,
    total_days: int,
    round_trips: int,
    wins: int,
) -> SimMetrics:
    mdd = max_drawdown(equity)
    cg = cagr(equity, len(equity))
    return SimMetrics(
        total_return=total_return(equity),
        cagr=cg,
        annual_volatility=annual_volatility(returns),
        sharpe=sharpe(returns),
        sortino=sortino(returns),
        max_drawdown=mdd,
        calmar=(cg / abs(mdd)) if mdd != 0 else None,
        exposure_pct=(in_market_days / total_days) if total_days else 0.0,
        round_trips=round_trips,
        win_rate=(wins / round_trips) if round_trips else None,
    )
