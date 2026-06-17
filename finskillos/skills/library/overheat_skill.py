"""RISK.OVERHEAT_ENTRY — the overheat-entry guard as a declarative skill (20.2b).

Byte-for-byte conversion of ``guards.overheat_guard`` — a categorical regime
match. Copy lifted verbatim.

* RISK.OVERHEAT_ENTRY-002  regime == RISK_ON_OVERHEAT   FAIL / ORANGE
* RISK.OVERHEAT_ENTRY-001  regime == DISTRIBUTION_RISK  WARN / YELLOW
* RISK.OVERHEAT_ENTRY-003  any other regime             PASS / GREEN
* RISK.OVERHEAT_ENTRY-000  (fallback) regime is None    INFO / UNKNOWN
"""

from __future__ import annotations

from finskillos.guards.base import (
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

SKILL_ID = "RISK.OVERHEAT_ENTRY"
VERSION = "overheat-v1-2026-06-17"

REGIME_RISK_ON_OVERHEAT = "RISK_ON_OVERHEAT"
REGIME_DISTRIBUTION_RISK = "DISTRIBUTION_RISK"


def _evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "regime": ctx.get("regime"),
        "decision_mode": ctx.get("decision_mode"),
    }


OVERHEAT_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Overheat entry — chase-exposure constraint by regime",
    reads=("regime", "decision_mode"),
    ladder=(
        Rule(
            rule_id="RISK.OVERHEAT_ENTRY-002",
            when=lambda ctx: ctx.get("regime") == REGIME_RISK_ON_OVERHEAT,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="시장이 RISK_ON_OVERHEAT — 추격형 노출 제약 구간입니다.",
            message=(
                "기존 강자 추세는 남아 있지만 추격형 노출은 기대 수익률 대비 위험이 큰 "
                "구간으로 보입니다."
            ),
            evidence=_evidence,
            watch_next=(
                "기존 강자의 stop / sizing 기준 점검",
                "추격형 노출의 sizing 제약 검토",
            ),
        ),
        Rule(
            rule_id="RISK.OVERHEAT_ENTRY-001",
            when=lambda ctx: ctx.get("regime") == REGIME_DISTRIBUTION_RISK,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="DISTRIBUTION_RISK — 공격적 노출 확대에 제약이 붙습니다.",
            message=(
                "추세는 유지되지만 모멘텀 약화 신호가 누적되어 노출 확대의 "
                "기대값이 낮아질 수 있습니다."
            ),
            evidence=_evidence,
            watch_next=(
                "주도 종목의 RSI 둔화 / 거래량 점검",
                "추격형 노출 검토 시 sizing 제약 확인",
            ),
        ),
        Rule(
            rule_id="RISK.OVERHEAT_ENTRY-003",
            when=lambda ctx: ctx.get("regime") is not None,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="현재 regime 기준 추격형 노출 제약은 낮습니다.",
            message=lambda ctx: (
                f"regime {ctx.get('regime')}은 추격형 노출 제약이 강하게 "
                "요구되는 상태가 아닙니다."
            ),
            evidence=_evidence,
        ),
    ),
    fallback=Rule(
        rule_id="RISK.OVERHEAT_ENTRY-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="시장 regime 정보가 없어 overheat 진입 제한을 평가할 수 없습니다.",
        message=(
            "RegimeService 결과가 누적되면 자동으로 overheat 노출 제약을 점검합니다."
        ),
        evidence=_evidence,
    ),
)
