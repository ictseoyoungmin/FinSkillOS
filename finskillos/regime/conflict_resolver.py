"""Conflict-resolution helpers for the Slice-05 Regime Engine.

Centralises the interpretation rules from docs/v2_1/06 §7. When two
opposing signals fire at once — RSI overheat with strong trend, falling
VIX with collapsing breadth, ... — the resolver returns a coherent
descriptive narrative rather than letting the engine flip-flop into a
contradictory state. The output is always interpretation text and
never a buy/sell directive.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from finskillos.regime import regime_rules as R


@dataclass(frozen=True)
class Scores:
    """Per-pillar 0-100 scores feeding the priority rules."""

    risk_on: Decimal
    overheat: Decimal
    risk_off: Decimal
    distribution: Decimal

    def dominant(self) -> str:
        """Return the strongest pillar name.

        Ties resolved in defensive order:
        ``risk_off`` > ``distribution`` > ``overheat`` > ``risk_on``.
        """
        ordered = (
            ("risk_off", self.risk_off),
            ("distribution", self.distribution),
            ("overheat", self.overheat),
            ("risk_on", self.risk_on),
        )
        winner = max(ordered, key=lambda kv: kv[1])
        return winner[0]


def conflict_summary(scores: Scores, *, regime: str) -> str:
    """Return a short interpretation tying the regime to the score split.

    Used by the engine to populate the `summary` field. Wording is
    deliberately descriptive — never `buy` / `sell` (SAFE-AC-001).
    """

    if regime == R.REGIME_RISK_ON_OVERHEAT:
        return (
            "상승 추세는 유지되고 있지만 RSI가 과열 구간에 들어가며 추격형 노출의 "
            "기대값이 낮아질 수 있습니다."
        )
    if regime == R.REGIME_DISTRIBUTION_RISK:
        return (
            "가격은 고점권을 유지하지만 모멘텀 약화 신호가 누적되어 분배 위험이 "
            "관찰됩니다."
        )
    if regime == R.REGIME_DEFENSIVE_TRANSITION:
        return (
            "변동성이 높아지고 단기 추세가 흔들리며 방어 전환 구간의 특성이 "
            "나타납니다."
        )
    if regime == R.REGIME_RISK_OFF:
        return (
            "위험 회피 신호가 다수 동시에 관찰되어 공격적 노출 확대보다 계좌 "
            "보호가 우선되는 환경입니다."
        )
    if regime == R.REGIME_PANIC:
        return (
            "공포와 강한 하락 압력이 함께 관찰됩니다. 추세 확인 없이 반등에만 "
            "기대는 접근은 신중해야 합니다."
        )
    if regime == R.REGIME_RECOVERY:
        return (
            "공포 구간 이후 단기 회복 신호가 보입니다. 확인 신호 없이 비중을 "
            "급격히 늘리는 접근은 신중해야 합니다."
        )
    if regime == R.REGIME_AGGRESSIVE_RISK_ON:
        return (
            "주도 섹터의 모멘텀이 강하며, 포지션 크기 관리만 유지된다면 공격적 "
            "운용이 가능한 구간으로 보입니다."
        )
    if regime == R.REGIME_HEALTHY_BULL:
        return (
            "지수가 EMA 위에서 안정적으로 형성되어 있고 변동성도 통제된 건강한 "
            "상승 구간으로 해석됩니다."
        )
    if regime == R.REGIME_UNKNOWN:
        return (
            "핵심 지표가 부족해 현재 시장 상태를 단정하기 어렵습니다. 데이터 "
            "보강 후 재평가가 필요합니다."
        )
    return "현재 지표 조합에 대한 해석 문구가 정의되지 않았습니다."


def coexists_overheat_with_trend(scores: Scores) -> bool:
    """True when both risk_on and overheat scores are simultaneously strong.

    This is the canonical conflict from docs/v2_1/06 §7 — momentum is
    strong and yet overheating. We surface this so the engine resolves
    it as `RISK_ON_OVERHEAT` instead of inferring a top.
    """
    return scores.risk_on >= Decimal("50") and scores.overheat >= Decimal("60")
