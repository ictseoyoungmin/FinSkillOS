"""EVENT.SCORE — the event-risk label band as a declarative classification skill.

Phase 20.4. ``EventRiskService`` assembles an ``event_risk_score`` (0–10) from
importance × portfolio-exposure × days-to-event × market-overheat weights (the
DB-coupled part stays in the service). The *labelling policy* — score → LOW /
MODERATE / HIGH / CRITICAL — is a pure band ladder, so it lives here as the first
fully-declarative classification skill (a ``label`` per rung). Parity-tested
against ``event_risk_service.risk_label_for_score``.

* EVENT.SCORE-004  >= 7.0  CRITICAL / RED
* EVENT.SCORE-003  >= 4.0  HIGH / ORANGE
* EVENT.SCORE-002  >= 2.0  MODERATE / YELLOW
* EVENT.SCORE-001  else    LOW / GREEN
* EVENT.SCORE-000  (fallback) no score → INFO / UNKNOWN
"""

from __future__ import annotations

from finskillos.guards.base import (
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_INFO,
)
from finskillos.skills.base import ANY, Rule, SkillContext, SkillSpec, band_rule

SKILL_ID = "EVENT.SCORE"
VERSION = "event-score-v1-2026-06-17"

_FEATURE = "event_risk_score"


def _evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "event_risk_score": ctx.num("event_risk_score"),
        "days_to_event": ctx.get("days_to_event"),
        "portfolio_exposure": ctx.get("portfolio_exposure"),
        "affected_tickers": ctx.get("affected_tickers"),
    }


def _band(rule_id: str, at_least, label: str, risk_level: str, note: str) -> Rule:
    return band_rule(
        rule_id,
        feature=_FEATURE,
        at_least=at_least,
        status=STATUS_INFO,
        risk_level=risk_level,
        label=label,
        title=f"이벤트 노출도 {label}.",
        message=lambda ctx: (
            f"이벤트 리스크 점수 {ctx.num('event_risk_score')}/10 — {note} "
            "(서술적 노출 참고치, 매매 신호 아님)."
        ),
        evidence=_evidence,
    )


EVENT_SCORE_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Event risk score — exposure band (LOW / MODERATE / HIGH / CRITICAL)",
    reads=("event_risk_score",),
    ladder=(
        _band("EVENT.SCORE-004", "7.0", "CRITICAL", RISK_RED, "점검 우선순위가 높은 노출 구간"),
        _band("EVENT.SCORE-003", "4.0", "HIGH", RISK_ORANGE, "노출 점검이 필요한 구간"),
        _band("EVENT.SCORE-002", "2.0", "MODERATE", RISK_YELLOW, "보통 수준의 노출"),
        _band("EVENT.SCORE-001", ANY, "LOW", RISK_GREEN, "노출이 낮은 구간"),
    ),
    fallback=Rule(
        rule_id="EVENT.SCORE-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="이벤트 리스크 점수를 계산할 수 없습니다.",
        message="이벤트와 보유 종목 연결 근거가 있으면 노출도가 자동으로 계산됩니다.",
        evidence=_evidence,
        label="UNKNOWN",
    ),
)
