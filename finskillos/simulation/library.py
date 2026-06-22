"""Built-in example strategy specs (Phase 21.2).

A small, descriptive starter library so the Quant Lab tab renders before the agent
can author specs (Phase 21.4). Each is a hypothesis expressed in the cockpit's own
feature vocabulary — exposure ON/OFF, never buy/sell.
"""

from __future__ import annotations

from finskillos.simulation.conditions import (
    All,
    Any,
    Compare,
    Condition,
    Cross,
)
from finskillos.simulation.engine import StrategySpec

STRATEGY_LIBRARY: tuple[StrategySpec, ...] = (
    StrategySpec(
        strategy_id="SMA_50_CROSS",
        name="SMA(50) 추세 추종",
        description=(
            "종가가 50일 이동평균을 상향 돌파하면 매수, 하향 돌파하면 매도. "
            "단순 추세 추종."
        ),
        universe=("NVDA",),
        entry=Cross("close", "above", "sma_50"),
        exit=Cross("close", "below", "sma_50"),
    ),
    StrategySpec(
        strategy_id="SMA_GOLDEN_20_50",
        name="골든크로스 SMA(20/50)",
        description=(
            "20일선이 50일선을 상향 돌파(골든크로스)하면 매수, "
            "하향 돌파(데드크로스)하면 매도."
        ),
        universe=("AAPL",),
        entry=Cross("sma_20", "above", "sma_50"),
        exit=Cross("sma_20", "below", "sma_50"),
    ),
    StrategySpec(
        strategy_id="RSI_MEAN_REVERT",
        name="RSI 과매도 반등",
        description=(
            "RSI(14)가 30 미만(과매도)이면 매수, 55를 넘으면 매도. 평균 회귀 "
            "(지표가 있는 구간에서만)."
        ),
        universe=("QQQ",),
        entry=Compare("rsi_14", "<", 30.0),
        exit=Compare("rsi_14", ">", 55.0),
    ),
    StrategySpec(
        strategy_id="TREND_STATE_FOLLOW",
        name="추세 상태 추종",
        description=(
            "지표의 trend_state가 BULLISH면 매수, BEARISH면 매도. 서술형 추세 "
            "분류를 그대로 따름."
        ),
        universe=("QQQ",),
        entry=Compare("trend", "==", "BULLISH"),
        exit=Compare("trend", "==", "BEARISH"),
    ),
    StrategySpec(
        strategy_id="RECOVERY_OVERSOLD",
        name="회복 국면 과매도",
        description=(
            "시장 regime이 RECOVERY이고 RSI(14)<35면 매수, RSI>60이면 매도. "
            "regime과 지표를 결합 (regime 히스토리가 있는 구간에서만)."
        ),
        universe=("QQQ",),
        entry=All((Compare("regime", "==", "RECOVERY"), Compare("rsi_14", "<", 35.0))),
        exit=Compare("rsi_14", ">", 60.0),
    ),
)

_BY_ID = {spec.strategy_id: spec for spec in STRATEGY_LIBRARY}


def get_strategy(strategy_id: str) -> StrategySpec | None:
    return _BY_ID.get(strategy_id)


def _op_text(op: str) -> str:
    return {
        "<": "<",
        "<=": "≤",
        ">": ">",
        ">=": "≥",
        "==": "=",
    }.get(op, op)


def condition_text(cond: Condition) -> str:
    """Render a condition as a short readable string for the UI / audit."""

    if isinstance(cond, Compare):
        return f"{cond.feature} {_op_text(cond.op)} {cond.value}"
    if isinstance(cond, Cross):
        arrow = "↑" if cond.direction == "above" else "↓"
        return f"{cond.feature} {arrow} {cond.reference}"
    if isinstance(cond, All):
        return " AND ".join(condition_text(t) for t in cond.terms)
    if isinstance(cond, Any):
        return " OR ".join(condition_text(t) for t in cond.terms)
    return "?"
