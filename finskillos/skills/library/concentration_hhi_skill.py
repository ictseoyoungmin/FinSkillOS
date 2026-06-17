"""RISK.CONCENTRATION_HHI — single-name concentration via the Herfindahl index.

A precision upgrade absorbed from legacy METRIC-015 (slice 284). The current
``concentration_guard`` measures *sector* concentration with weight bands; this
skill adds the portfolio-level **Herfindahl index** (∑ wᵢ²) + max single-name
weight, a more precise concentration measure. It is a *new* rule (no existing
guard equivalent), authored skill-first — a live guard counterpart can follow at
the Phase 20.2 service swap.

Thresholds (legacy METRIC-015 §6):
* max_weight > 0.5  → single name over half the book
* hhi > 0.25        → concentration score high

Rule ladder:
* RISK.CONCENTRATION_HHI-003  max_weight > 0.5  WARN / YELLOW — single name dominates
* RISK.CONCENTRATION_HHI-002  hhi > 0.25        WARN / YELLOW — HHI concentration high
* RISK.CONCENTRATION_HHI-001  else (data present) PASS / GREEN — diversified
* RISK.CONCENTRATION_HHI-000  (fallback) INFO / UNKNOWN — no positions/total
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from finskillos.guards.base import (
    RISK_GREEN,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.skills.base import Rule, SkillContext, SkillSpec

SKILL_ID = "RISK.CONCENTRATION_HHI"
VERSION = "concentration-hhi-v1-2026-06-17"

MAX_WEIGHT_LIMIT = Decimal("0.5")
HHI_LIMIT = Decimal("0.25")


def _pos_field(pos: object, name: str) -> object | None:
    """Read a position field from either a PositionRiskInput (the live shape) or
    a plain mapping (test fixtures)."""

    if hasattr(pos, name):
        return getattr(pos, name)
    if hasattr(pos, "get"):
        return pos.get(name)  # type: ignore[attr-defined]
    return None


def _derive_concentration(ctx: SkillContext) -> Mapping[str, object]:
    """Compute HHI + max single-name weight from positions / total value.

    ``positions`` is a sequence of PositionRiskInput objects (live) or mappings
    (tests), each with ``ticker`` + ``market_value``. Leaves the features absent
    (→ fallback) when there is nothing to weigh.
    """

    positions = ctx.get("positions") or []
    total = ctx.num("total_value")
    if not positions or total is None or total <= 0:
        return {}
    weights: list[tuple[str, Decimal]] = []
    for pos in positions:
        mv = _pos_field(pos, "market_value")
        if mv is None:
            continue
        ticker = str(_pos_field(pos, "ticker") or "?")
        weights.append((ticker, Decimal(str(mv)) / total))
    if not weights:
        return {}
    hhi = sum((w * w for _, w in weights), Decimal("0"))
    top_ticker, top_weight = max(weights, key=lambda item: item[1])
    return {
        "hhi": hhi.quantize(Decimal("0.0001")),
        "max_weight": top_weight,
        "top_ticker": top_ticker,
        "position_count": len(weights),
    }


def _evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "hhi": ctx.num("hhi"),
        "max_weight": ctx.num("max_weight"),
        "top_ticker": ctx.get("top_ticker"),
        "position_count": ctx.get("position_count"),
    }


def _pct(ctx: SkillContext, key: str) -> str:
    value = ctx.num(key)
    return f"{value * 100:.1f}%" if value is not None else "N/A"


_WATCH = (
    "종목별 비중 상한 점검",
    "신규 종목 노출 확대 시 단일 종목 비중 제약 검토",
)

CONCENTRATION_HHI_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Concentration — Herfindahl index + max single-name weight",
    reads=("positions", "total_value"),
    derive=_derive_concentration,
    ladder=(
        Rule(
            rule_id="RISK.CONCENTRATION_HHI-003",
            when=lambda ctx: (
                ctx.num("max_weight") is not None
                and ctx.num("max_weight") > MAX_WEIGHT_LIMIT
            ),
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="단일 종목 비중이 과반입니다.",
            message=lambda ctx: (
                f"{ctx.get('top_ticker')} 비중이 {_pct(ctx, 'max_weight')}로 "
                "포트폴리오의 절반을 넘습니다. 단일 종목 손실이 계좌 전체에 크게 "
                "전이될 수 있습니다."
            ),
            evidence=_evidence,
            watch_next=_WATCH,
        ),
        Rule(
            rule_id="RISK.CONCENTRATION_HHI-002",
            when=lambda ctx: (
                ctx.num("hhi") is not None and ctx.num("hhi") > HHI_LIMIT
            ),
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="HHI 기준 집중도가 높습니다.",
            message=lambda ctx: (
                f"Herfindahl 지수가 {ctx.num('hhi')}로 0.25를 초과해 소수 종목 "
                "집중도가 높습니다. 분산 정도를 점검하세요."
            ),
            evidence=_evidence,
            watch_next=_WATCH,
        ),
        Rule(
            rule_id="RISK.CONCENTRATION_HHI-001",
            when=lambda ctx: ctx.num("hhi") is not None,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="종목 집중도가 분산 범위입니다.",
            message=lambda ctx: (
                f"Herfindahl 지수 {ctx.num('hhi')}, 최대 종목 비중 "
                f"{_pct(ctx, 'max_weight')}로 집중 리스크가 낮은 편입니다."
            ),
            evidence=_evidence,
        ),
    ),
    fallback=Rule(
        rule_id="RISK.CONCENTRATION_HHI-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="집중도를 계산할 포지션 / 총액 정보가 없습니다.",
        message=(
            "보유 포지션과 총 평가액이 기록되면 HHI 집중도가 자동으로 계산됩니다."
        ),
        evidence=lambda ctx: {
            "position_count": ctx.get("position_count"),
            "total_value": ctx.get("total_value"),
        },
    ),
)
