"""RISK.GOAL_PROTECTION — the goal-protection guard as a declarative skill (20.2b).

Byte-for-byte conversion of ``guards.goal_guard`` behind the registry seam,
parity-tested. Progress thresholds + copy are lifted verbatim.

* RISK.GOAL_PROTECTION-004  >= 100  BLOCKED / RED   — goal complete
* RISK.GOAL_PROTECTION-003  >= 90   FAIL / ORANGE   — protection mode
* RISK.GOAL_PROTECTION-002  >= 70   WARN / YELLOW    — late-stage caution
* RISK.GOAL_PROTECTION-001  else    PASS / GREEN     — normal operating band
* RISK.GOAL_PROTECTION-000  (fallback) INFO / UNKNOWN — no progress reading
"""

from __future__ import annotations

from finskillos.guards.base import (
    DEFAULT_GOAL_COMPLETE_PCT,
    DEFAULT_GOAL_PROTECTION_PCT,
    DEFAULT_GOAL_WARN_PCT,
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
)
from finskillos.skills.base import ANY, Rule, SkillContext, SkillSpec, band_rule

SKILL_ID = "RISK.GOAL_PROTECTION"
VERSION = "goal-v1-2026-06-17"


def _evidence(ctx: SkillContext) -> dict[str, object]:
    return {
        "goal_progress_pct": ctx.num("goal_progress_pct"),
        "warn_threshold": DEFAULT_GOAL_WARN_PCT,
        "protection_threshold": DEFAULT_GOAL_PROTECTION_PCT,
        "complete_threshold": DEFAULT_GOAL_COMPLETE_PCT,
    }


def _msg(template: str):
    def _build(ctx: SkillContext) -> str:
        return template.format(progress=ctx.num("goal_progress_pct"))

    return _build


GOAL_SKILL = SkillSpec(
    skill_id=SKILL_ID,
    version=VERSION,
    title="Goal protection — progress-band operating posture",
    reads=("goal_progress_pct",),
    ladder=(
        band_rule(
            "RISK.GOAL_PROTECTION-004",
            feature="goal_progress_pct",
            at_least=DEFAULT_GOAL_COMPLETE_PCT,
            status=STATUS_BLOCKED,
            risk_level=RISK_RED,
            title="목표 달성 — 챌린지 완료 단계입니다.",
            message=_msg(
                "목표 진행률이 {progress:.1f}%로 달성/초과 상태입니다. "
                "추가 공격적 운용보다 이익 보호가 우선되는 단계입니다."
            ),
            evidence=_evidence,
            watch_next=(
                "다음 목표 설정 전 냉각 기간 유지",
                "이익 보호 기준 / 분산 상태 검토",
            ),
        ),
        band_rule(
            "RISK.GOAL_PROTECTION-003",
            feature="goal_progress_pct",
            at_least=DEFAULT_GOAL_PROTECTION_PCT,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="목표 근접 구간 — 보호 모드로 전환할 시점입니다.",
            message=_msg(
                "목표 진행률 {progress:.1f}%로 목표에 매우 근접했습니다. "
                "수익 극대화보다 손실 회피가 우선되는 운영이 어울립니다."
            ),
            evidence=_evidence,
            watch_next=(
                "drawdown guard 민감도 상향",
                "고위험 추격형 노출 제약",
            ),
        ),
        band_rule(
            "RISK.GOAL_PROTECTION-002",
            feature="goal_progress_pct",
            at_least=DEFAULT_GOAL_WARN_PCT,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="목표 진행률이 상승 구간 — 무리한 위험 확대 경계.",
            message=_msg(
                "목표 진행률 {progress:.1f}%로 후반부에 진입했습니다. "
                "추가 위험 확대보다 이익 보호 기준 점검이 우선입니다."
            ),
            evidence=_evidence,
            watch_next=(
                "이벤트 전 과대 포지션 점검",
                "현금 비중 최소치 회복 여부",
            ),
        ),
        band_rule(
            "RISK.GOAL_PROTECTION-001",
            feature="goal_progress_pct",
            at_least=ANY,
            status=STATUS_PASS,
            risk_level=RISK_GREEN,
            title="목표 진행률이 정상 운영 구간에 있습니다.",
            message=_msg(
                "목표 진행률 {progress:.1f}%로 기본 운영 모드를 유지할 수 있는 구간입니다."
            ),
            evidence=_evidence,
        ),
    ),
    fallback=Rule(
        rule_id="RISK.GOAL_PROTECTION-000",
        when=lambda _ctx: True,
        status=STATUS_INFO,
        risk_level=RISK_UNKNOWN,
        title="목표 진행률 정보가 없어 보호 모드를 평가할 수 없습니다.",
        message=(
            "Goal Tracker가 최신 portfolio_snapshots를 읽고 있는지 "
            "또는 target_value가 설정되어 있는지 점검하세요."
        ),
        evidence=lambda _ctx: {"goal_progress_pct": None},
    ),
)
