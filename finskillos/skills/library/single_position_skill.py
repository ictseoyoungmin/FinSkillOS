"""RISK.SINGLE_POSITION — the single-position-limit guard as a declarative skill.

Byte-for-byte conversion of ``guards.single_position_guard`` (20.2b). The derive
step scans positions for over-limit / approaching names and pre-formats the
offender strings + evidence so the rungs stay declarative.

* RISK.SINGLE_POSITION-002  any position > limit        FAIL / ORANGE
* RISK.SINGLE_POSITION-001  any position in 90%..limit  WARN / YELLOW
* RISK.SINGLE_POSITION-000  (fallback) all within limit  PASS / GREEN
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from finskillos.guards.base import (
    RISK_GREEN,
    RISK_ORANGE,
    RISK_YELLOW,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.skills.base import Rule, SkillContext, SkillSpec

SKILL_ID = "RISK.SINGLE_POSITION"
VERSION = "single-position-v1-2026-06-17"

_WARN_RATIO_OF_LIMIT = Decimal("0.9")


def _offenders(positions) -> str:
    return ", ".join(f"{p.ticker}({p.market_value:,.0f} KRW)" for p in positions)


def _derive(ctx: SkillContext) -> Mapping[str, object]:
    limit = ctx.num("single_position_limit")
    positions = ctx.get("positions") or ()
    warn_threshold = (limit * _WARN_RATIO_OF_LIMIT).quantize(Decimal("0.01"))
    over = [p for p in positions if p.market_value > limit]
    approaching = [
        p for p in positions if warn_threshold < p.market_value <= limit
    ]
    return {
        "_limit": limit,
        "_warn_threshold": warn_threshold,
        "_position_count": len(positions),
        "_over_count": len(over),
        "_approaching_count": len(approaching),
        "_over_offenders": _offenders(over),
        "_approaching_offenders": _offenders(approaching),
        "_over_tickers": [p.ticker for p in over],
        "_over_values": {p.ticker: p.market_value for p in over},
        "_approaching_tickers": [p.ticker for p in approaching],
        "_approaching_values": {p.ticker: p.market_value for p in approaching},
    }


SINGLE_POSITION_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Single position limit — per-name size ceiling",
    reads=("positions", "single_position_limit"),
    derive=_derive,
    ladder=(
        Rule(
            rule_id="RISK.SINGLE_POSITION-002",
            when=lambda ctx: bool(ctx.get("_over_count")),
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="단일 종목 한도를 초과한 포지션이 있습니다.",
            message=lambda ctx: (
                f"{ctx.get('_over_offenders')} 포지션이 단일 종목 한도 "
                f"{ctx.num('_limit'):,.0f} KRW를 초과합니다. "
                "신규 추가보다 사이즈 점검이 우선되는 상태입니다."
            ),
            evidence=lambda ctx: {
                "limit": ctx.num("_limit"),
                "over_limit_tickers": ctx.get("_over_tickers"),
                "over_limit_values": ctx.get("_over_values"),
            },
            watch_next=(
                "한도 초과 종목의 thesis / stop 기준 재확인",
                "신규 동일 테마 추가 진입 제한",
            ),
        ),
        Rule(
            rule_id="RISK.SINGLE_POSITION-001",
            when=lambda ctx: bool(ctx.get("_approaching_count")),
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="단일 종목 한도 근접 포지션이 있습니다.",
            message=lambda ctx: (
                f"{ctx.get('_approaching_offenders')} 포지션이 한도 "
                f"{ctx.num('_limit'):,.0f} KRW의 90%를 넘어섰습니다. "
                "추가 비중 확대 전에 사이즈를 점검하세요."
            ),
            evidence=lambda ctx: {
                "limit": ctx.num("_limit"),
                "warn_threshold": ctx.num("_warn_threshold"),
                "approaching_tickers": ctx.get("_approaching_tickers"),
                "approaching_values": ctx.get("_approaching_values"),
            },
            watch_next=("한도 근접 종목의 추가 진입 시 사이즈 재계산",),
        ),
    ),
    fallback=Rule(
        rule_id="RISK.SINGLE_POSITION-000",
        when=lambda _ctx: True,
        status=STATUS_PASS,
        risk_level=RISK_GREEN,
        title="모든 포지션이 단일 종목 한도 이내입니다.",
        message=lambda ctx: (
            f"현재 모든 포지션이 한도 {ctx.num('_limit'):,.0f} KRW 안에서 "
            "유지되고 있습니다."
        ),
        evidence=lambda ctx: {
            "limit": ctx.num("_limit"),
            "position_count": ctx.get("_position_count"),
        },
    ),
)
