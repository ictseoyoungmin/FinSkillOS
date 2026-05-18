"""Pure rule-first Market Regime Engine (Slice 05).

Translates a set of stored market indicators (SPY/QQQ/SMH trend states,
RSIs, VIX close, DXY and US10Y trend states, optional breadth /
momentum scores) into a deterministic, interpretation-first market
state.

Design rules (docs/v2_1/06 + .devmd/05):

* Rule-first, not LLM-first — every regime decision is a function of
  the inputs, fully reproducible from a fixture.
* Descriptive output only — `RegimeOutput` carries `summary`,
  `what_happened`, `what_it_means`, `watch_next`, plus a structured
  `evidence` dict so the UI / Risk Guards can drill down. No field
  ever stores a buy/sell instruction; the safety check in
  ``finskillos.regime.regime_rules.FORBIDDEN_WORDS`` is enforced by
  tests in ``tests/test_regime_engine.py``.
* Conflict handling — when overheat coexists with a strong trend the
  engine returns ``RISK_ON_OVERHEAT`` with a ``HOLD_WINNERS`` mode,
  not a bearish reversal call (docs/v2_1/06 §7).
* Missing data tolerance — the engine never crashes on ``None``
  inputs; the dominant rule path simply receives fewer signals and
  the confidence score drops accordingly. With too little data the
  result is ``UNKNOWN`` rather than a guess.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from finskillos.regime import regime_rules as R
from finskillos.regime.conflict_resolver import (
    Scores,
    coexists_overheat_with_trend,
    conflict_summary,
)

# Minimum required inputs for a non-UNKNOWN classification.
MIN_INPUTS_REQUIRED = 4


@dataclass(frozen=True)
class RegimeInput:
    """Snapshot of market indicators consumed by the regime engine.

    Fields are intentionally typed ``Optional`` so the service can pass
    whatever Slice 04 actually managed to compute. Required-vs-optional
    semantics live inside the engine, not the DTO.
    """

    spy_trend_state: str | None
    qqq_trend_state: str | None
    smh_trend_state: str | None
    spy_rsi_14: Decimal | None
    qqq_rsi_14: Decimal | None
    smh_rsi_14: Decimal | None
    vix_close: Decimal | None
    dxy_trend_state: str | None
    us10y_trend_state: str | None
    breadth_score: Decimal | None = None
    momentum_score: Decimal | None = None


@dataclass(frozen=True)
class RegimeOutput:
    """Interpretation-first regime read model.

    ``evidence`` is a JSON-serialisable map of the indicators that
    actually fed the rule — handy for the Control Room "Why this
    regime?" drilldown without re-running the engine.
    """

    regime: str
    confidence: Decimal
    decision_mode: str
    risk_level: str
    summary: str
    what_happened: str
    what_it_means: str
    watch_next: tuple[str, ...]
    evidence: dict[str, str | Decimal | None] = field(default_factory=dict)
    rule_version: str = R.RULE_VERSION

    def is_actionable(self) -> bool:
        """True when confidence is high enough to drive a Control Room banner."""
        return (
            self.regime != R.REGIME_UNKNOWN
            and self.confidence >= R.CONFIDENCE_LOW_THRESHOLD
        )


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _count_present(inputs: RegimeInput) -> int:
    return sum(
        1
        for v in (
            inputs.spy_trend_state,
            inputs.qqq_trend_state,
            inputs.smh_trend_state,
            inputs.spy_rsi_14,
            inputs.qqq_rsi_14,
            inputs.smh_rsi_14,
            inputs.vix_close,
            inputs.dxy_trend_state,
            inputs.us10y_trend_state,
        )
        if v is not None
    )


def _bullish_trend_votes(inputs: RegimeInput) -> int:
    return sum(
        1
        for t in (
            inputs.spy_trend_state,
            inputs.qqq_trend_state,
            inputs.smh_trend_state,
        )
        if t in R.BULLISH_TRENDS
    )


def _strict_bullish_votes(inputs: RegimeInput) -> int:
    """Count of indices whose trend is strictly ``BULLISH`` (excludes WEAK_BULLISH)."""
    return sum(
        1
        for t in (
            inputs.spy_trend_state,
            inputs.qqq_trend_state,
            inputs.smh_trend_state,
        )
        if t == R.TREND_BULLISH
    )


def _bearish_trend_votes(inputs: RegimeInput) -> int:
    return sum(
        1
        for t in (
            inputs.spy_trend_state,
            inputs.qqq_trend_state,
            inputs.smh_trend_state,
        )
        if t in R.BEARISH_TRENDS
    )


def _rsi_overheat_votes(inputs: RegimeInput) -> int:
    return sum(
        1
        for v in (inputs.qqq_rsi_14, inputs.smh_rsi_14, inputs.spy_rsi_14)
        if v is not None and v >= R.RSI_OVERHEAT
    )


def _rsi_oversold_votes(inputs: RegimeInput) -> int:
    return sum(
        1
        for v in (inputs.qqq_rsi_14, inputs.smh_rsi_14, inputs.spy_rsi_14)
        if v is not None and v <= R.RSI_OVERSOLD
    )


def _compute_scores(inputs: RegimeInput) -> Scores:
    risk_on = Decimal("0")
    overheat = Decimal("0")
    risk_off = Decimal("0")
    distribution = Decimal("0")

    # --- risk-on signals -------------------------------------------------
    risk_on += Decimal("20") * _bullish_trend_votes(inputs)
    if inputs.vix_close is not None:
        if inputs.vix_close < R.VIX_CALM:
            risk_on += Decimal("20")
        elif inputs.vix_close < R.VIX_CAUTION:
            risk_on += Decimal("10")
    if inputs.momentum_score is not None and inputs.momentum_score > Decimal("0"):
        risk_on += min(Decimal("20"), inputs.momentum_score)
    if inputs.breadth_score is not None and inputs.breadth_score >= Decimal("60"):
        risk_on += Decimal("10")

    # --- overheat signals -------------------------------------------------
    overheat += Decimal("25") * _rsi_overheat_votes(inputs)
    if inputs.vix_close is not None and inputs.vix_close < R.VIX_CALM:
        overheat += Decimal("10")
    if inputs.momentum_score is not None and inputs.momentum_score >= Decimal("15"):
        overheat += Decimal("10")

    # --- risk-off signals ------------------------------------------------
    risk_off += Decimal("20") * _bearish_trend_votes(inputs)
    if inputs.vix_close is not None:
        if inputs.vix_close >= R.VIX_PANIC:
            risk_off += Decimal("30")
        elif inputs.vix_close >= R.VIX_RISK_OFF:
            risk_off += Decimal("20")
        elif inputs.vix_close >= R.VIX_CAUTION:
            risk_off += Decimal("10")
    risk_off += Decimal("10") * _rsi_oversold_votes(inputs)
    if inputs.dxy_trend_state in R.BULLISH_TRENDS:
        risk_off += Decimal("5")
    if inputs.us10y_trend_state in R.BULLISH_TRENDS:
        risk_off += Decimal("5")

    # --- distribution signals --------------------------------------------
    # Bullish trend but momentum fading or breadth narrowing.
    if (
        _bullish_trend_votes(inputs) >= 2
        and inputs.momentum_score is not None
        and inputs.momentum_score <= Decimal("0")
    ):
        distribution += Decimal("40")
    if (
        _bullish_trend_votes(inputs) >= 1
        and inputs.breadth_score is not None
        and inputs.breadth_score < Decimal("45")
    ):
        distribution += Decimal("30")

    return Scores(
        risk_on=_clamp(risk_on),
        overheat=_clamp(overheat),
        risk_off=_clamp(risk_off),
        distribution=_clamp(distribution),
    )


def _clamp(
    value: Decimal,
    *,
    lower: Decimal = Decimal("0"),
    upper: Decimal = Decimal("100"),
) -> Decimal:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


def _classify_state(inputs: RegimeInput, scores: Scores) -> str:
    """Apply the rule priority ladder from docs/v2_1/06 §3.

    Priorities run from most defensive to most aggressive so that a
    PANIC/RISK_OFF state never gets masked by stronger bullish signals
    elsewhere in the input — that mirrors the "loss-avoidance first"
    principle of the rulebook.
    """

    bullish_votes = _bullish_trend_votes(inputs)
    bearish_votes = _bearish_trend_votes(inputs)
    overheat_votes = _rsi_overheat_votes(inputs)

    # PANIC — strongest risk-off signal: panic VIX plus bearish indices.
    if (
        inputs.vix_close is not None
        and inputs.vix_close >= R.VIX_PANIC
        and bearish_votes >= 2
    ):
        return R.REGIME_PANIC

    # RISK_OFF — high VIX with deteriorating trend.
    if (
        inputs.vix_close is not None
        and inputs.vix_close >= R.VIX_RISK_OFF
        and bullish_votes == 0
        and bearish_votes >= 1
    ):
        return R.REGIME_RISK_OFF

    # DEFENSIVE_TRANSITION — caution-level VIX, trend weakening but not yet bearish-dominant.
    if (
        inputs.vix_close is not None
        and inputs.vix_close >= R.VIX_CAUTION
        and bearish_votes >= 1
        and bullish_votes <= 1
    ):
        return R.REGIME_DEFENSIVE_TRANSITION

    # RISK_ON_OVERHEAT — bullish trend with multiple RSI overheats.
    if bullish_votes >= 2 and overheat_votes >= 2:
        return R.REGIME_RISK_ON_OVERHEAT
    if coexists_overheat_with_trend(scores):
        return R.REGIME_RISK_ON_OVERHEAT

    # DISTRIBUTION_RISK — bullish price but momentum/breadth degrading.
    if scores.distribution >= Decimal("30") and bullish_votes >= 1:
        return R.REGIME_DISTRIBUTION_RISK

    # AGGRESSIVE_RISK_ON — strict bullish stack across all three indices,
    # calm VIX, and QQQ or SMH RSI in the aggressive band (>= 65). The
    # strict-trend requirement is what separates this state from a
    # plain HEALTHY_BULL: it takes a confirmed leadership push.
    if (
        _strict_bullish_votes(inputs) >= 2
        and inputs.qqq_trend_state == R.TREND_BULLISH
        and (inputs.smh_trend_state == R.TREND_BULLISH or inputs.spy_trend_state == R.TREND_BULLISH)
        and inputs.vix_close is not None
        and inputs.vix_close < R.VIX_CAUTION
        and _qqq_or_smh_in(
            inputs,
            low=Decimal("65"),
            high=R.RSI_AGGRESSIVE_HIGH,
        )
    ):
        return R.REGIME_AGGRESSIVE_RISK_ON

    # HEALTHY_BULL — bullish trend, calm VIX, RSI in healthy band.
    if (
        bullish_votes >= 2
        and (inputs.vix_close is None or inputs.vix_close < R.VIX_CAUTION)
        and _qqq_or_smh_in(
            inputs,
            low=R.RSI_HEALTHY_LOW,
            high=R.RSI_HEALTHY_HIGH,
        )
    ):
        return R.REGIME_HEALTHY_BULL

    # RECOVERY — VIX cooling, neutral/weak-bullish trend, RSI rebuilding.
    if (
        inputs.vix_close is not None
        and inputs.vix_close <= R.VIX_CAUTION
        and bearish_votes == 0
        and _rsi_in_band(
            inputs.qqq_rsi_14, low=R.RSI_RECOVERY_LOW, high=R.RSI_RECOVERY_HIGH
        )
    ):
        return R.REGIME_RECOVERY

    # Default — if we still see a bullish stack, fall through to HEALTHY_BULL.
    if bullish_votes >= 2:
        return R.REGIME_HEALTHY_BULL

    return R.REGIME_UNKNOWN


def _qqq_or_smh_in(inputs: RegimeInput, *, low: Decimal, high: Decimal) -> bool:
    return any(
        _rsi_in_band(v, low=low, high=high)
        for v in (inputs.qqq_rsi_14, inputs.smh_rsi_14, inputs.spy_rsi_14)
    )


def _rsi_in_band(value: Decimal | None, *, low: Decimal, high: Decimal) -> bool:
    return value is not None and low <= value <= high


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


def _confidence(inputs: RegimeInput, regime: str, scores: Scores) -> Decimal:
    if regime == R.REGIME_UNKNOWN:
        return Decimal("0")

    base = R.CONFIDENCE_FULL
    # Penalty for missing inputs.
    missing = 9 - _count_present(inputs)
    base -= R.CONFIDENCE_PER_MISSING_INPUT * Decimal(max(missing, 0))

    # Penalty when the dominant pillar barely wins.
    dominant_score = max(
        scores.risk_off, scores.distribution, scores.overheat, scores.risk_on
    )
    runner_up = sorted(
        (scores.risk_off, scores.distribution, scores.overheat, scores.risk_on),
        reverse=True,
    )[1]
    margin = dominant_score - runner_up
    if margin < Decimal("15"):
        base -= R.CONFIDENCE_PER_CONFLICT

    return _clamp(base, lower=R.CONFIDENCE_FLOOR, upper=R.CONFIDENCE_FULL)


# ---------------------------------------------------------------------------
# Interpretation strings
# ---------------------------------------------------------------------------


_WHAT_HAPPENED: dict[str, str] = {
    R.REGIME_PANIC: (
        "변동성 지수가 공포 구간으로 진입했고 주요 지수 추세가 함께 무너지고 있습니다."
    ),
    R.REGIME_RISK_OFF: (
        "VIX가 위험 회피 구간으로 올라섰고 SPY/QQQ 단기 추세가 약화되고 있습니다."
    ),
    R.REGIME_DEFENSIVE_TRANSITION: (
        "VIX가 경계 구간으로 올라서며 단기 추세가 흔들리고 있습니다."
    ),
    R.REGIME_DISTRIBUTION_RISK: (
        "지수는 고점권을 유지하지만 모멘텀 약화 또는 breadth 축소가 함께 관찰됩니다."
    ),
    R.REGIME_RISK_ON_OVERHEAT: (
        "주도 지수의 RSI가 70 이상으로 올라서며 추격 진입의 기대값이 낮아질 수 있습니다."
    ),
    R.REGIME_AGGRESSIVE_RISK_ON: (
        "주도 섹터의 모멘텀이 강하게 유지되고 VIX는 안정 구간에 머무르고 있습니다."
    ),
    R.REGIME_HEALTHY_BULL: (
        "지수가 EMA 위에서 안정적으로 형성되어 있고 RSI가 건강한 모멘텀 구간에 있습니다."
    ),
    R.REGIME_RECOVERY: (
        "공포 구간 이후 VIX가 식어가고 RSI가 회복 구간으로 진입하고 있습니다."
    ),
    R.REGIME_UNKNOWN: (
        "현재 보유한 지표만으로는 시장 상태를 단정하기 어렵습니다."
    ),
}

_WHAT_IT_MEANS: dict[str, str] = {
    R.REGIME_PANIC: (
        "추세 확인 없이 반등에만 기대는 접근은 신중해야 하며 계좌 보호가 우선됩니다."
    ),
    R.REGIME_RISK_OFF: (
        "신규 공격적 운용보다 현금 비중 확보와 기존 포지션 점검이 우선입니다."
    ),
    R.REGIME_DEFENSIVE_TRANSITION: (
        "신규 추격 진입을 줄이고 약한 포지션의 stop 기준을 점검할 시점입니다."
    ),
    R.REGIME_DISTRIBUTION_RISK: (
        "기존 강자의 비중을 축소하거나 익절 기준을 점검하는 운영이 어울리는 구간입니다."
    ),
    R.REGIME_RISK_ON_OVERHEAT: (
        "기존 강자는 유지하되 신규 추격 진입은 제한하는 운영이 어울립니다."
    ),
    R.REGIME_AGGRESSIVE_RISK_ON: (
        "포지션 크기 관리만 유지된다면 주도 종목 중심 운용이 가능한 구간입니다."
    ),
    R.REGIME_HEALTHY_BULL: (
        "정상 운용이 가능하며, 분산과 단일 종목 한도만 유지하면 충분합니다."
    ),
    R.REGIME_RECOVERY: (
        "확인 신호가 누적될 때마다 소액 단위로 비중을 점진적으로 회복할 수 있습니다."
    ),
    R.REGIME_UNKNOWN: (
        "필요 데이터가 들어올 때까지 적극적인 신규 운용보다 점검 작업이 우선입니다."
    ),
}

_WATCH_NEXT: dict[str, tuple[str, ...]] = {
    R.REGIME_PANIC: (
        "VIX가 안정 구간으로 돌아오는지 확인",
        "SPY/QQQ가 EMA20을 회복하는지 확인",
        "현금 비중과 단일 종목 노출도 점검",
    ),
    R.REGIME_RISK_OFF: (
        "VIX 추세 반전 여부",
        "주요 지수의 EMA20 회복 여부",
        "현금 비중과 drawdown guard 상태",
    ),
    R.REGIME_DEFENSIVE_TRANSITION: (
        "VIX가 caution 구간을 벗어나는지",
        "QQQ가 EMA20 위에서 안정되는지",
        "약한 포지션의 stop / thesis 점검",
    ),
    R.REGIME_DISTRIBUTION_RISK: (
        "거래량 동반 음봉 발생 여부",
        "주도 종목의 RSI 둔화 정도",
        "breadth 회복 여부",
    ),
    R.REGIME_RISK_ON_OVERHEAT: (
        "기존 강자의 stop 기준 점검",
        "신규 추격 진입 제한 유지",
        "주도 섹터 RSI가 70 위에서 머무는 기간",
    ),
    R.REGIME_AGGRESSIVE_RISK_ON: (
        "포지션 크기와 단일 종목 비중",
        "주도 섹터 모멘텀 지속 여부",
        "변동성 확대 신호",
    ),
    R.REGIME_HEALTHY_BULL: (
        "주도 섹터 RSI가 healthy 구간을 유지하는지",
        "단일 종목 1천만원 한도 점검",
        "VIX가 caution 구간으로 올라서는지",
    ),
    R.REGIME_RECOVERY: (
        "VIX가 안정 구간으로 더 내려가는지",
        "QQQ RSI가 55 위에서 안정되는지",
        "거래량 동반 양봉 발생 여부",
    ),
    R.REGIME_UNKNOWN: (
        "SPY/QQQ/SMH 지표 갱신 상태",
        "VIX 데이터 수집 상태",
        "지표 갱신 후 재평가",
    ),
}


def _evidence(inputs: RegimeInput, scores: Scores) -> dict[str, Any]:
    return {
        "spy_trend_state": inputs.spy_trend_state,
        "qqq_trend_state": inputs.qqq_trend_state,
        "smh_trend_state": inputs.smh_trend_state,
        "spy_rsi_14": inputs.spy_rsi_14,
        "qqq_rsi_14": inputs.qqq_rsi_14,
        "smh_rsi_14": inputs.smh_rsi_14,
        "vix_close": inputs.vix_close,
        "dxy_trend_state": inputs.dxy_trend_state,
        "us10y_trend_state": inputs.us10y_trend_state,
        "breadth_score": inputs.breadth_score,
        "momentum_score": inputs.momentum_score,
        "risk_on_score": scores.risk_on,
        "overheat_score": scores.overheat,
        "risk_off_score": scores.risk_off,
        "distribution_score": scores.distribution,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_regime(inputs: RegimeInput) -> RegimeOutput:
    """Pure rule-based classifier — same input always produces same output."""

    scores = _compute_scores(inputs)
    present = _count_present(inputs)

    if present < MIN_INPUTS_REQUIRED:
        return RegimeOutput(
            regime=R.REGIME_UNKNOWN,
            confidence=Decimal("0"),
            decision_mode=R.regime_to_mode(R.REGIME_UNKNOWN),
            risk_level=R.regime_to_risk_level(R.REGIME_UNKNOWN),
            summary=conflict_summary(scores, regime=R.REGIME_UNKNOWN),
            what_happened=_WHAT_HAPPENED[R.REGIME_UNKNOWN],
            what_it_means=_WHAT_IT_MEANS[R.REGIME_UNKNOWN],
            watch_next=_WATCH_NEXT[R.REGIME_UNKNOWN],
            evidence=_evidence(inputs, scores),
        )

    regime = _classify_state(inputs, scores)
    confidence = _confidence(inputs, regime, scores)

    return RegimeOutput(
        regime=regime,
        confidence=confidence,
        decision_mode=R.regime_to_mode(regime),
        risk_level=R.regime_to_risk_level(regime),
        summary=conflict_summary(scores, regime=regime),
        what_happened=_WHAT_HAPPENED[regime],
        what_it_means=_WHAT_IT_MEANS[regime],
        watch_next=_WATCH_NEXT[regime],
        evidence=_evidence(inputs, scores),
    )
