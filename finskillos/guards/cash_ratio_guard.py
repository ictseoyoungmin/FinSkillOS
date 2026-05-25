"""Cash Ratio Guard — minimum-cash buffer check.

Compares ``cash_value / total_value`` against the configured floor and
flags when liquidity drops below the safety band. Output is descriptive
only — the guard never says "raise cash by selling X", it just reports
that the current cash ratio is below the configured limit.
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    DEFAULT_CASH_FAIL_THRESHOLD,
    GUARD_CASH_RATIO,
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


def evaluate(inputs: GuardInput) -> GuardResult:
    if inputs.total_value <= 0:
        return GuardResult(
            guard_name=GUARD_CASH_RATIO,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="포트폴리오 총평가금액이 0이라 현금비중을 계산할 수 없습니다.",
            message=(
                "포지션이나 현금이 입력되지 않은 상태입니다. "
                "기본 portfolio 입력 후 다시 점검하세요."
            ),
            evidence={
                "cash_value": inputs.cash_value,
                "total_value": inputs.total_value,
                "min_cash_ratio": inputs.min_cash_ratio,
            },
            watch_next=("최신 portfolio snapshot이 입력되어 있는지 확인",),
        )

    ratio = (inputs.cash_value / inputs.total_value).quantize(Decimal("0.0001"))
    min_ratio = inputs.min_cash_ratio
    fail_floor = DEFAULT_CASH_FAIL_THRESHOLD

    if ratio >= min_ratio:
        return GuardResult(
            guard_name=GUARD_CASH_RATIO,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="현금비중이 최소 기준을 충족합니다.",
            message=(
                f"현재 현금비중 {ratio:.2%}은 목표 최소치 {min_ratio:.0%} 이상을 "
                "유지하고 있습니다."
            ),
            evidence={
                "cash_ratio": ratio,
                "min_cash_ratio": min_ratio,
                "cash_value": inputs.cash_value,
                "total_value": inputs.total_value,
            },
        )

    if ratio >= fail_floor:
        return GuardResult(
            guard_name=GUARD_CASH_RATIO,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="현금비중이 목표 최소치 아래로 내려갔습니다.",
            message=(
                f"현재 현금비중 {ratio:.2%}이 목표 최소치 {min_ratio:.0%}보다 낮습니다. "
                "급락/이벤트 대응 여력을 점검하세요."
            ),
            evidence={
                "cash_ratio": ratio,
                "min_cash_ratio": min_ratio,
                "cash_value": inputs.cash_value,
                "total_value": inputs.total_value,
            },
            watch_next=(
                "유동성 버퍼가 목표 하한 아래인지 확인",
                "이벤트 캘린더 대비 현금 여력 점검",
            ),
        )

    return GuardResult(
        guard_name=GUARD_CASH_RATIO,
        status=STATUS_FAIL,
        risk_level=RISK_ORANGE,
        title="현금비중이 위험 수준까지 낮아졌습니다.",
        message=(
            f"현재 현금비중 {ratio:.2%}이 안전 한계 {fail_floor:.0%} 미만입니다. "
            "급락이나 이벤트 발생 시 대응 여력이 매우 제한적입니다."
        ),
        evidence={
            "cash_ratio": ratio,
            "min_cash_ratio": min_ratio,
            "fail_floor": fail_floor,
            "cash_value": inputs.cash_value,
            "total_value": inputs.total_value,
        },
        watch_next=(
            "유동성 버퍼 목표치와 현재 격차 확인",
            "공격적 노출 확대 제약 유지",
        ),
    )
