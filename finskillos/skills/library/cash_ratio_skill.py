"""RISK.CASH_RATIO — the cash-ratio guard as a declarative skill (20.2b).

Byte-for-byte conversion of ``guards.cash_ratio_guard``. The PASS threshold is the
account's own ``min_cash_ratio`` (an input, not a constant), so the rungs use
predicates rather than fixed bands; the derive step computes the ratio.

* RISK.CASH_RATIO-001  ratio >= min_cash_ratio  PASS / GREEN
* RISK.CASH_RATIO-002  ratio >= 0.05 floor      WARN / YELLOW
* RISK.CASH_RATIO-003  else                     FAIL / ORANGE
* RISK.CASH_RATIO-000  (fallback) total<=0      INFO / UNKNOWN
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

from finskillos.guards.base import (
    DEFAULT_CASH_FAIL_THRESHOLD,
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

SKILL_ID = "RISK.CASH_RATIO"
VERSION = "cash-ratio-v1-2026-06-17"


def _derive(ctx: SkillContext) -> Mapping[str, object]:
    total = ctx.num("total_value")
    cash = ctx.num("cash_value")
    if total is None or total <= 0 or cash is None:
        return {}
    return {"cash_ratio": (cash / total).quantize(Decimal("0.0001"))}


def _ev_ok(ctx: SkillContext) -> dict[str, object]:
    return {
        "cash_ratio": ctx.num("cash_ratio"),
        "min_cash_ratio": ctx.get("min_cash_ratio"),
        "cash_value": ctx.get("cash_value"),
        "total_value": ctx.get("total_value"),
    }


def _ev_fail(ctx: SkillContext) -> dict[str, object]:
    return {
        "cash_ratio": ctx.num("cash_ratio"),
        "min_cash_ratio": ctx.get("min_cash_ratio"),
        "fail_floor": DEFAULT_CASH_FAIL_THRESHOLD,
        "cash_value": ctx.get("cash_value"),
        "total_value": ctx.get("total_value"),
    }


def _ratio(ctx: SkillContext) -> Decimal:
    return ctx.num("cash_ratio")


def _min(ctx: SkillContext) -> Decimal:
    return ctx.num("min_cash_ratio")


CASH_RATIO_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Cash ratio — liquidity buffer vs the account minimum",
    reads=("cash_value", "total_value", "min_cash_ratio"),
    derive=_derive,
    ladder=(
        Rule(
            rule_id="RISK.CASH_RATIO-001",
            when=lambda ctx: (
                ctx.num("cash_ratio") is not None
                and ctx.num("cash_ratio") >= ctx.num("min_cash_ratio")
            ),
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="현금비중이 최소 기준을 충족합니다.",
            message=lambda ctx: (
                f"현재 현금비중 {_ratio(ctx):.2%}은 목표 최소치 {_min(ctx):.0%} 이상을 "
                "유지하고 있습니다."
            ),
            evidence=_ev_ok,
        ),
        Rule(
            rule_id="RISK.CASH_RATIO-002",
            when=lambda ctx: (
                ctx.num("cash_ratio") is not None
                and ctx.num("cash_ratio") >= DEFAULT_CASH_FAIL_THRESHOLD
            ),
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="현금비중이 목표 최소치 아래로 내려갔습니다.",
            message=lambda ctx: (
                f"현재 현금비중 {_ratio(ctx):.2%}이 목표 최소치 {_min(ctx):.0%}보다 낮습니다. "
                "급락/이벤트 대응 여력을 점검하세요."
            ),
            evidence=_ev_ok,
            watch_next=(
                "유동성 버퍼가 목표 하한 아래인지 확인",
                "이벤트 캘린더 대비 현금 여력 점검",
            ),
        ),
        Rule(
            rule_id="RISK.CASH_RATIO-003",
            when=lambda ctx: ctx.num("cash_ratio") is not None,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="현금비중이 위험 수준까지 낮아졌습니다.",
            message=lambda ctx: (
                f"현재 현금비중 {_ratio(ctx):.2%}이 안전 한계 "
                f"{DEFAULT_CASH_FAIL_THRESHOLD:.0%} 미만입니다. "
                "급락이나 이벤트 발생 시 대응 여력이 매우 제한적입니다."
            ),
            evidence=_ev_fail,
            watch_next=(
                "유동성 버퍼 목표치와 현재 격차 확인",
                "공격적 노출 확대 제약 유지",
            ),
        ),
    ),
    fallback=Rule(
        rule_id="RISK.CASH_RATIO-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="포트폴리오 총평가금액이 0이라 현금비중을 계산할 수 없습니다.",
        message=(
            "포지션이나 현금이 입력되지 않은 상태입니다. "
            "기본 portfolio 입력 후 다시 점검하세요."
        ),
        evidence=lambda ctx: {
            "cash_value": ctx.get("cash_value"),
            "total_value": ctx.get("total_value"),
            "min_cash_ratio": ctx.get("min_cash_ratio"),
        },
        watch_next=("최신 portfolio snapshot이 입력되어 있는지 확인",),
    ),
)
