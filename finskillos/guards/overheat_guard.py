"""Overheat Entry Guard — flags aggressive risk expansion in overheat regimes.

Fires when the current ``regime`` is ``RISK_ON_OVERHEAT`` (or, more
softly, ``DISTRIBUTION_RISK``). The guard re-states the operating
constraint that chase-style exposure needs review — it does NOT issue
an exit / sell directive (SAFE-AC-001).
"""

from __future__ import annotations

from finskillos.guards.base import (
    GUARD_OVERHEAT_ENTRY,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
    GuardInput,
    GuardResult,
)

REGIME_RISK_ON_OVERHEAT = "RISK_ON_OVERHEAT"
REGIME_DISTRIBUTION_RISK = "DISTRIBUTION_RISK"


def evaluate(inputs: GuardInput) -> GuardResult:
    regime = inputs.regime
    evidence = {
        "regime": regime,
        "decision_mode": inputs.decision_mode,
    }

    if regime is None:
        return GuardResult(
            guard_name=GUARD_OVERHEAT_ENTRY,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="시장 regime 정보가 없어 overheat 진입 제한을 평가할 수 없습니다.",
            message=(
                "RegimeService 결과가 누적되면 자동으로 overheat 노출 제약을 점검합니다."
            ),
            evidence=evidence,
        )

    if regime == REGIME_RISK_ON_OVERHEAT:
        return GuardResult(
            guard_name=GUARD_OVERHEAT_ENTRY,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="시장이 RISK_ON_OVERHEAT — 추격형 노출 제약 구간입니다.",
            message=(
                "기존 강자 추세는 남아 있지만 추격형 노출은 기대 수익률 대비 위험이 큰 "
                "구간으로 보입니다."
            ),
            evidence=evidence,
            watch_next=(
                "기존 강자의 stop / sizing 기준 점검",
                "추격형 노출의 sizing 제약 검토",
            ),
        )

    if regime == REGIME_DISTRIBUTION_RISK:
        return GuardResult(
            guard_name=GUARD_OVERHEAT_ENTRY,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="DISTRIBUTION_RISK — 공격적 노출 확대에 제약이 붙습니다.",
            message=(
                "추세는 유지되지만 모멘텀 약화 신호가 누적되어 노출 확대의 "
                "기대값이 낮아질 수 있습니다."
            ),
            evidence=evidence,
            watch_next=(
                "주도 종목의 RSI 둔화 / 거래량 점검",
                "추격형 노출 검토 시 sizing 제약 확인",
            ),
        )

    return GuardResult(
        guard_name=GUARD_OVERHEAT_ENTRY,
        status=STATUS_PASS,
        risk_level=RISK_GREEN,
        title="현재 regime 기준 추격형 노출 제약은 낮습니다.",
        message=(
            f"regime {regime}은 추격형 노출 제약이 강하게 요구되는 상태가 아닙니다."
        ),
        evidence=evidence,
    )
