"""Single Position Limit Guard — per-symbol absolute KRW limit.

The user policy is "single position should not exceed 10,000,000 KRW";
the limit is configurable via ``GuardInput.single_position_limit``. The
guard surfaces every position above the limit so the Risk Firewall can
list offenders, but it never instructs the user to reduce — it only
reports the breach.
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    GUARD_SINGLE_POSITION,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
    GuardInput,
    GuardResult,
)

# Warn band starts at 90% of the limit so users see a heads-up before
# they trip the hard ceiling.
_WARN_RATIO_OF_LIMIT = Decimal("0.9")


def evaluate(inputs: GuardInput) -> GuardResult:
    limit = inputs.single_position_limit
    warn_threshold = (limit * _WARN_RATIO_OF_LIMIT).quantize(Decimal("0.01"))

    over_limit = tuple(
        p for p in inputs.positions if p.market_value > limit
    )
    approaching = tuple(
        p
        for p in inputs.positions
        if warn_threshold < p.market_value <= limit
    )

    if over_limit:
        offenders = ", ".join(
            f"{p.ticker}({p.market_value:,.0f} KRW)" for p in over_limit
        )
        return GuardResult(
            guard_name=GUARD_SINGLE_POSITION,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="단일 종목 한도를 초과한 포지션이 있습니다.",
            message=(
                f"{offenders} 포지션이 단일 종목 한도 {limit:,.0f} KRW를 초과합니다. "
                "신규 추가보다 사이즈 점검이 우선되는 상태입니다."
            ),
            evidence={
                "limit": limit,
                "over_limit_tickers": [p.ticker for p in over_limit],
                "over_limit_values": {
                    p.ticker: p.market_value for p in over_limit
                },
            },
            watch_next=(
                "한도 초과 종목의 thesis / stop 기준 재확인",
                "신규 동일 테마 추가 진입 제한",
            ),
        )

    if approaching:
        offenders = ", ".join(
            f"{p.ticker}({p.market_value:,.0f} KRW)" for p in approaching
        )
        return GuardResult(
            guard_name=GUARD_SINGLE_POSITION,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="단일 종목 한도 근접 포지션이 있습니다.",
            message=(
                f"{offenders} 포지션이 한도 {limit:,.0f} KRW의 90%를 넘어섰습니다. "
                "추가 비중 확대 전에 사이즈를 점검하세요."
            ),
            evidence={
                "limit": limit,
                "warn_threshold": warn_threshold,
                "approaching_tickers": [p.ticker for p in approaching],
                "approaching_values": {
                    p.ticker: p.market_value for p in approaching
                },
            },
            watch_next=(
                "한도 근접 종목의 추가 진입 시 사이즈 재계산",
            ),
        )

    return GuardResult(
        guard_name=GUARD_SINGLE_POSITION,
        status=STATUS_PASS,
        risk_level=RISK_GREEN,
        title="모든 포지션이 단일 종목 한도 이내입니다.",
        message=(
            f"현재 모든 포지션이 한도 {limit:,.0f} KRW 안에서 유지되고 있습니다."
        ),
        evidence={
            "limit": limit,
            "position_count": len(inputs.positions),
        },
    )
