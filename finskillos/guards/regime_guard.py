"""Regime Risk Guard — surfaces the current market regime as a constraint.

Reads the latest ``regime`` / ``regime_risk_level`` / ``decision_mode``
the orchestrator pulled from MarketRegimeRepository and translates them
into a guard result. The guard never re-classifies the regime — that
work belongs to Slice 05; this guard only re-renders the verdict in
the Risk Firewall vocabulary so the same fact lives in one place.
"""

from __future__ import annotations

from finskillos.guards.base import (
    GUARD_REGIME_RISK,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
    GuardInput,
    GuardResult,
)

# Risk-level → (status, guard-level) mapping.
_REGIME_LEVEL_MAP = {
    RISK_RED: (STATUS_FAIL, RISK_RED),
    RISK_ORANGE: (STATUS_FAIL, RISK_ORANGE),
    RISK_YELLOW: (STATUS_WARN, RISK_YELLOW),
    RISK_GREEN: (STATUS_PASS, RISK_GREEN),
    RISK_UNKNOWN: (STATUS_INFO, RISK_UNKNOWN),
}


def evaluate(inputs: GuardInput) -> GuardResult:
    if inputs.regime is None or inputs.regime_risk_level is None:
        return GuardResult(
            guard_name=GUARD_REGIME_RISK,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="시장 regime 정보가 아직 수집되지 않았습니다.",
            message=(
                "RegimeService.evaluate_today_regime이 실행되어 market_regimes에 "
                "결과가 누적되면 자동으로 점검합니다."
            ),
            evidence={
                "regime": None,
                "regime_risk_level": None,
                "decision_mode": inputs.decision_mode,
            },
        )

    status, level = _REGIME_LEVEL_MAP.get(
        inputs.regime_risk_level, (STATUS_INFO, RISK_UNKNOWN)
    )
    evidence = {
        "regime": inputs.regime,
        "regime_risk_level": inputs.regime_risk_level,
        "decision_mode": inputs.decision_mode,
    }

    if status == STATUS_PASS:
        return GuardResult(
            guard_name=GUARD_REGIME_RISK,
            status=status,
            risk_level=level,
            title="시장 regime이 우호적인 구간입니다.",
            message=(
                f"현재 regime {inputs.regime} / 운영 모드 {inputs.decision_mode}에서 "
                "기본 검토 모드가 가능한 환경입니다."
            ),
            evidence=evidence,
        )

    if status == STATUS_WARN:
        return GuardResult(
            guard_name=GUARD_REGIME_RISK,
            status=status,
            risk_level=level,
            title="시장 regime이 주의 구간으로 진입했습니다.",
            message=(
                f"현재 regime {inputs.regime}는 운영 모드 {inputs.decision_mode}로 "
                "공격적 노출 확대에는 제약 검토가 필요합니다."
            ),
            evidence=evidence,
            watch_next=(
                "주도 섹터 RSI / VIX 추이 점검",
                "추격형 노출 제약 유지",
            ),
        )

    if status == STATUS_FAIL:
        return GuardResult(
            guard_name=GUARD_REGIME_RISK,
            status=status,
            risk_level=level,
            title="시장 regime이 방어 구간입니다.",
            message=(
                f"현재 regime {inputs.regime}는 운영 모드 {inputs.decision_mode}로 "
                "계좌 보호가 우선되는 환경입니다."
            ),
            evidence=evidence,
            watch_next=(
                "현금 비중 / drawdown guard 상태 점검",
                "공격적 노출 확대 제약 유지",
            ),
        )

    return GuardResult(
        guard_name=GUARD_REGIME_RISK,
        status=status,
        risk_level=level,
        title="시장 regime 정보를 해석할 수 없습니다.",
        message=(
            f"regime_risk_level={inputs.regime_risk_level!r}이 알려진 값이 아닙니다."
        ),
        evidence=evidence,
    )
