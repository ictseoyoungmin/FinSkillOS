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
    # --- Designed additions (Slice 336) — distinct market logics --------------
    StrategySpec(
        strategy_id="EMA_GOLDEN_20_60",
        name="EMA 골든크로스 (20/60)",
        description=(
            "EMA(20)이 EMA(60)을 상향 돌파하면 매수, 하향 돌파하면 매도. 지수이동평균"
            "이라 단순이동평균보다 추세 전환에 빠르게 반응하는 추세 추종."
        ),
        universe=("QQQ",),
        entry=Cross("ema_20", "above", "ema_60"),
        exit=Cross("ema_20", "below", "ema_60"),
    ),
    StrategySpec(
        strategy_id="TREND_PULLBACK_RSI",
        name="상승추세 눌림목 매수",
        description=(
            "상승 추세(BULLISH/WEAK_BULLISH)에서 RSI(14)가 45 아래로 눌릴 때 매수, "
            "RSI가 70을 넘어 과열되거나 추세가 BEARISH로 꺾이면 매도. 추세 안에서 "
            "저가 매수를 노리는 결합 전략."
        ),
        universe=("NVDA",),
        entry=All(
            (
                Any(
                    (
                        Compare("trend", "==", "BULLISH"),
                        Compare("trend", "==", "WEAK_BULLISH"),
                    )
                ),
                Compare("rsi_14", "<", 45.0),
            )
        ),
        exit=Any(
            (Compare("rsi_14", ">", 70.0), Compare("trend", "==", "BEARISH"))
        ),
    ),
    StrategySpec(
        strategy_id="BREAKOUT_SMA20_MOMENTUM",
        name="모멘텀 확인 돌파",
        description=(
            "종가가 20일 이동평균을 상향 돌파하면서 RSI(14)>50으로 모멘텀이 확인될 "
            "때만 매수, 20일선을 하향 이탈하면 매도. 모멘텀 필터로 가짜 돌파를 거른다."
        ),
        universe=("AAPL",),
        entry=All(
            (Cross("close", "above", "sma_20"), Compare("rsi_14", ">", 50.0))
        ),
        exit=Cross("close", "below", "sma_20"),
    ),
    StrategySpec(
        strategy_id="DIP_BUY_UPTREND",
        name="상승추세 낙폭 매수",
        description=(
            "상승 추세에서 고점 대비 8% 이상 눌릴 때(drawdown<-8%) 매수, 고점 -2% "
            "이내로 회복하면 매도. 추세를 거스르지 않는 낙폭 저가 매수."
        ),
        universe=("NVDA",),
        entry=All(
            (
                Compare("drawdown_pct", "<", -8.0),
                Any(
                    (
                        Compare("trend", "==", "BULLISH"),
                        Compare("trend", "==", "WEAK_BULLISH"),
                    )
                ),
            )
        ),
        exit=Compare("drawdown_pct", ">", -2.0),
    ),
    StrategySpec(
        strategy_id="EMA60_TREND_RECLAIM",
        name="EMA(60) 추세 회복",
        description=(
            "종가가 EMA(60)을 상향 돌파(장기 추세 회복)하면 매수, 하향 이탈하면 매도. "
            "분기 추세선 기준의 느린 추세 추종."
        ),
        universe=("MSFT",),
        entry=Cross("close", "above", "ema_60"),
        exit=Cross("close", "below", "ema_60"),
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
