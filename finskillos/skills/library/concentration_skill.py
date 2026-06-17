"""RISK.SECTOR_CONCENTRATION — the sector-concentration guard as a declarative
skill (20.2b).

Byte-for-byte conversion of ``guards.concentration_guard``. Positions are bucketed
by sector (None → UNCLASSIFIED) in the derive step, which also resolves the
heaviest sector + share; the rungs read those.

* RISK.SECTOR_CONCENTRATION-003  heaviest > 50%   FAIL / ORANGE
* RISK.SECTOR_CONCENTRATION-002  heaviest > 35%   WARN / YELLOW
* RISK.SECTOR_CONCENTRATION-001  heaviest <= 35%  PASS / GREEN
* RISK.SECTOR_CONCENTRATION-004  positions but 0 value  INFO / UNKNOWN
* RISK.SECTOR_CONCENTRATION-000  (fallback) no positions INFO / UNKNOWN
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from finskillos.guards.base import (
    DEFAULT_SECTOR_FAIL_PCT,
    DEFAULT_SECTOR_WARN_PCT,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.skills.base import Rule, SkillContext, SkillSpec

SKILL_ID = "RISK.SECTOR_CONCENTRATION"
VERSION = "sector-concentration-v1-2026-06-17"

UNCLASSIFIED = "UNCLASSIFIED"


def _derive(ctx: SkillContext) -> Mapping[str, object]:
    positions = ctx.get("positions") or ()
    if not positions:
        return {"_conc_state": "EMPTY"}
    buckets: dict[str, Decimal] = {}
    for p in positions:
        key = p.sector or UNCLASSIFIED
        buckets[key] = buckets.get(key, Decimal("0")) + p.market_value
    total = sum(buckets.values(), Decimal("0"))
    if total <= 0:
        return {"_conc_state": "ZERO", "_position_count": len(positions)}
    shares = {
        sector: (value / total).quantize(Decimal("0.0001"))
        for sector, value in buckets.items()
    }
    heaviest_sector, heaviest_share = max(shares.items(), key=lambda kv: kv[1])
    return {
        "_conc_state": "OK",
        "_shares": shares,
        "_heaviest_sector": heaviest_sector,
        "_heaviest_share": heaviest_share,
    }


def _base_evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "sector_shares": ctx.get("_shares"),
        "heaviest_sector": ctx.get("_heaviest_sector"),
        "heaviest_share": ctx.get("_heaviest_share"),
        "warn_threshold": DEFAULT_SECTOR_WARN_PCT,
        "fail_threshold": DEFAULT_SECTOR_FAIL_PCT,
    }


def _ok(ctx: SkillContext) -> bool:
    return ctx.get("_conc_state") == "OK"


def _share(ctx: SkillContext) -> Decimal:
    return ctx.num("_heaviest_share")


CONCENTRATION_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Sector concentration — heaviest-sector share band",
    reads=("positions",),
    derive=_derive,
    ladder=(
        Rule(
            rule_id="RISK.SECTOR_CONCENTRATION-003",
            when=lambda ctx: _ok(ctx) and _share(ctx) > DEFAULT_SECTOR_FAIL_PCT,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="섹터 집중도가 위험 수준까지 높아졌습니다.",
            message=lambda ctx: (
                f"{ctx.get('_heaviest_sector')} 섹터가 포지션 평가금액의 "
                f"{_share(ctx):.1%}를 차지합니다. 한 가지 테마 위험에 묶일 "
                "가능성이 큽니다."
            ),
            evidence=_base_evidence,
            watch_next=(
                "동일 테마 추가 진입 제한",
                "현금/방어 섹터로 분산 여지 점검",
            ),
        ),
        Rule(
            rule_id="RISK.SECTOR_CONCENTRATION-002",
            when=lambda ctx: _ok(ctx) and _share(ctx) > DEFAULT_SECTOR_WARN_PCT,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="특정 섹터 비중이 빠르게 커지고 있습니다.",
            message=lambda ctx: (
                f"{ctx.get('_heaviest_sector')} 섹터가 {_share(ctx):.1%}로 일반 "
                "한계를 넘어섰습니다. 같은 테마 추가 진입은 집중 위험을 키울 수 "
                "있습니다."
            ),
            evidence=_base_evidence,
            watch_next=(
                "동일 테마 종목 추가 진입 검토",
                "포트폴리오 내 분산 비중 재점검",
            ),
        ),
        Rule(
            rule_id="RISK.SECTOR_CONCENTRATION-001",
            when=_ok,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="섹터 집중도가 안전 구간에 있습니다.",
            message=lambda ctx: (
                f"가장 큰 섹터 비중은 {ctx.get('_heaviest_sector')} "
                f"{_share(ctx):.1%}로 한계 이내입니다."
            ),
            evidence=_base_evidence,
        ),
        Rule(
            rule_id="RISK.SECTOR_CONCENTRATION-004",
            when=lambda ctx: ctx.get("_conc_state") == "ZERO",
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="포지션 평가금액이 0이라 섹터 노출을 계산할 수 없습니다.",
            message="positions.market_value 값이 입력되어 있는지 점검하세요.",
            evidence=lambda ctx: {"position_count": ctx.get("_position_count")},
        ),
    ),
    fallback=Rule(
        rule_id="RISK.SECTOR_CONCENTRATION-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="포지션이 없어 섹터 노출을 계산할 수 없습니다.",
        message="포트폴리오에 포지션이 등록되면 섹터 집중도를 자동으로 점검합니다.",
        evidence=lambda _ctx: {"position_count": 0},
    ),
)
