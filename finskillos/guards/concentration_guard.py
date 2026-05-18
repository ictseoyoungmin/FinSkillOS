"""Sector Concentration Guard — per-sector exposure ceiling.

Bucketed by ``position.sector`` (None becomes ``UNCLASSIFIED``). The
guard reports the heaviest sector and its share of total portfolio
market value. Positions without a sector are still counted toward the
total so the user can see when a large slice of the book has no sector
tagging yet.
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    DEFAULT_SECTOR_FAIL_PCT,
    DEFAULT_SECTOR_WARN_PCT,
    GUARD_SECTOR_CONCENTRATION,
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

UNCLASSIFIED = "UNCLASSIFIED"


def evaluate(inputs: GuardInput) -> GuardResult:
    if not inputs.positions:
        return GuardResult(
            guard_name=GUARD_SECTOR_CONCENTRATION,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="포지션이 없어 섹터 노출을 계산할 수 없습니다.",
            message="포트폴리오에 포지션이 등록되면 섹터 집중도를 자동으로 점검합니다.",
            evidence={"position_count": 0},
        )

    buckets: dict[str, Decimal] = {}
    for p in inputs.positions:
        key = p.sector or UNCLASSIFIED
        buckets[key] = buckets.get(key, Decimal("0")) + p.market_value
    total_position_value = sum(buckets.values(), Decimal("0"))
    if total_position_value <= 0:
        return GuardResult(
            guard_name=GUARD_SECTOR_CONCENTRATION,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="포지션 평가금액이 0이라 섹터 노출을 계산할 수 없습니다.",
            message="positions.market_value 값이 입력되어 있는지 점검하세요.",
            evidence={"position_count": len(inputs.positions)},
        )

    shares = {
        sector: (value / total_position_value).quantize(Decimal("0.0001"))
        for sector, value in buckets.items()
    }
    heaviest_sector, heaviest_share = max(shares.items(), key=lambda kv: kv[1])

    base_evidence = {
        "sector_shares": shares,
        "heaviest_sector": heaviest_sector,
        "heaviest_share": heaviest_share,
        "warn_threshold": DEFAULT_SECTOR_WARN_PCT,
        "fail_threshold": DEFAULT_SECTOR_FAIL_PCT,
    }

    if heaviest_share > DEFAULT_SECTOR_FAIL_PCT:
        return GuardResult(
            guard_name=GUARD_SECTOR_CONCENTRATION,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="섹터 집중도가 위험 수준까지 높아졌습니다.",
            message=(
                f"{heaviest_sector} 섹터가 포지션 평가금액의 {heaviest_share:.1%}를 "
                f"차지합니다. 한 가지 테마 위험에 묶일 가능성이 큽니다."
            ),
            evidence=base_evidence,
            watch_next=(
                "동일 테마 추가 진입 제한",
                "현금/방어 섹터로 분산 여지 점검",
            ),
        )

    if heaviest_share > DEFAULT_SECTOR_WARN_PCT:
        return GuardResult(
            guard_name=GUARD_SECTOR_CONCENTRATION,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="특정 섹터 비중이 빠르게 커지고 있습니다.",
            message=(
                f"{heaviest_sector} 섹터가 {heaviest_share:.1%}로 일반 한계를 넘어섰습니다. "
                "같은 테마 추가 진입은 집중 위험을 키울 수 있습니다."
            ),
            evidence=base_evidence,
            watch_next=(
                "동일 테마 종목 추가 진입 검토",
                "포트폴리오 내 분산 비중 재점검",
            ),
        )

    return GuardResult(
        guard_name=GUARD_SECTOR_CONCENTRATION,
        status=STATUS_PASS,
        risk_level=RISK_GREEN,
        title="섹터 집중도가 안전 구간에 있습니다.",
        message=(
            f"가장 큰 섹터 비중은 {heaviest_sector} {heaviest_share:.1%}로 한계 이내입니다."
        ),
        evidence=base_evidence,
    )
