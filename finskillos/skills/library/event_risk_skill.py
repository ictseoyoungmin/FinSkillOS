"""RISK.EVENT_RISK — the event-risk guard as a declarative skill (20.2b).

Byte-for-byte conversion of ``guards.event_risk_guard``. Always INFO/GREEN
(descriptive exposure context, never a WARN/FAIL trade signal). Reads the
``EventRiskSummary`` the service stashes on the context.

* RISK.EVENT_RISK-002  connected + upcoming events  INFO / GREEN — monitoring
* RISK.EVENT_RISK-001  connected, no events         INFO / GREEN — neutral
* RISK.EVENT_RISK-000  (fallback) not connected      INFO / GREEN — deferred
"""

from __future__ import annotations

from finskillos.guards.base import RISK_GREEN, STATUS_INFO
from finskillos.skills.base import Rule, SkillContext, SkillSpec

SKILL_ID = "RISK.EVENT_RISK"
VERSION = "event-risk-v1-2026-06-17"


def _summary(ctx: SkillContext):
    return ctx.get("event_risk")


def _connected_title(ctx: SkillContext) -> str:
    s = _summary(ctx)
    return (
        f"예정 이벤트 {s.upcoming_count}건 모니터링 중 "
        f"(최고 노출 {s.highest_label})."
    )


def _connected_evidence(ctx: SkillContext) -> dict[str, object]:
    s = _summary(ctx)
    affected = ", ".join(s.affected_tickers) if s.affected_tickers else "—"
    return {
        "events_table_connected": True,
        "upcoming_count": s.upcoming_count,
        "holdings_relevant_count": s.holdings_relevant_count,
        "highest_label": s.highest_label,
        "highest_score": s.highest_score,
        "nearest_days": s.nearest_days,
        "affected_tickers": affected,
    }


EVENT_RISK_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Event risk — descriptive Catalyst Watch exposure",
    reads=("event_risk",),
    ladder=(
        Rule(
            rule_id="RISK.EVENT_RISK-002",
            when=lambda ctx: (
                _summary(ctx) is not None
                and _summary(ctx).connected
                and _summary(ctx).upcoming_count > 0
            ),
            status=STATUS_INFO,
            risk_level=RISK_GREEN,
            title=_connected_title,
            message=(
                "Catalyst Watch 노출도는 보유 종목과 이벤트 연결을 바탕으로 한 서술적 "
                "참고 지표입니다. 가격 방향 예측이 아니라 점검이 필요한 노출 구간을 "
                "표시합니다."
            ),
            evidence=_connected_evidence,
            watch_next=(
                "보유 종목과 연결된 고노출 이벤트의 일정/상태를 Catalyst Watch에서 확인",
            ),
        ),
        Rule(
            rule_id="RISK.EVENT_RISK-001",
            when=lambda ctx: (
                _summary(ctx) is not None and _summary(ctx).connected
            ),
            status=STATUS_INFO,
            risk_level=RISK_GREEN,
            title="추적 중인 예정 이벤트가 없습니다.",
            message=(
                "Catalyst Watch에 등록된 다가오는 이벤트가 없어 이벤트 노출도는 현재 "
                "중립입니다. System Ops 이벤트 시드 이후 다시 평가됩니다."
            ),
            evidence=lambda ctx: {
                "events_table_connected": True,
                "upcoming_count": 0,
            },
            watch_next=(
                "Catalyst Watch에 다가오는 이벤트가 등록되면 노출도를 자동 갱신",
            ),
        ),
    ),
    fallback=Rule(
        rule_id="RISK.EVENT_RISK-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="Catalyst Watch 이벤트 근거가 아직 없습니다.",
        message=(
            "이벤트 노출도 평가는 Catalyst Watch의 예정 이벤트와 보유 종목 연결 "
            "근거가 있을 때 서술적 참고 지표로 표시됩니다."
        ),
        evidence=lambda _ctx: {
            "events_table_connected": False,
            "event_exposure_status": "missing_catalyst_watch_evidence",
        },
        watch_next=(
            "Catalyst Watch 이벤트 시드 또는 refresh 이후 이벤트 노출도 재평가",
        ),
    ),
)
