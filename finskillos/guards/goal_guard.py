"""Goal Protection Guard — escalating warnings as the goal approaches.

Pulls ``goal_progress_pct`` (0-100, Decimal) and emits a descriptive
operating-mode constraint. The wording is intentionally *do not expand
risk* style; the guard does not tell the user to liquidate or exit, it
just notes that approaching the goal means the cost of a loss is now
larger than the upside of a stretch.

Thresholds align with docs/v2_1/06 §10 goal phases:

* < 70%       : PASS  / GREEN — normal growth posture
* 70% – 90%   : WARN  / YELLOW — risk expansion caution
* 90% – 100%  : FAIL  / ORANGE — protection mode
* >= 100%     : BLOCKED / RED — challenge complete, defensive only
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    DEFAULT_GOAL_COMPLETE_PCT,
    DEFAULT_GOAL_PROTECTION_PCT,
    DEFAULT_GOAL_WARN_PCT,
    GUARD_GOAL_PROTECTION,
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
    GuardInput,
    GuardResult,
)


def evaluate(inputs: GuardInput) -> GuardResult:
    progress = inputs.goal_progress_pct
    if progress is None:
        return GuardResult(
            guard_name=GUARD_GOAL_PROTECTION,
            status=STATUS_INFO,
            risk_level=RISK_UNKNOWN,
            title="목표 진행률 정보가 없어 보호 모드를 평가할 수 없습니다.",
            message=(
                "Goal Tracker가 최신 portfolio_snapshots를 읽고 있는지 "
                "또는 target_value가 설정되어 있는지 점검하세요."
            ),
            evidence={"goal_progress_pct": None},
        )

    progress = Decimal(progress)
    base_evidence = {
        "goal_progress_pct": progress,
        "warn_threshold": DEFAULT_GOAL_WARN_PCT,
        "protection_threshold": DEFAULT_GOAL_PROTECTION_PCT,
        "complete_threshold": DEFAULT_GOAL_COMPLETE_PCT,
    }

    if progress >= DEFAULT_GOAL_COMPLETE_PCT:
        return GuardResult(
            guard_name=GUARD_GOAL_PROTECTION,
            status=STATUS_BLOCKED,
            risk_level=RISK_RED,
            title="목표 달성 — 챌린지 완료 단계입니다.",
            message=(
                f"목표 진행률이 {progress:.1f}%로 달성/초과 상태입니다. "
                "추가 공격적 운용보다 이익 보호가 우선되는 단계입니다."
            ),
            evidence=base_evidence,
            watch_next=(
                "다음 목표 설정 전 냉각 기간 유지",
                "이익 보호 / 분산 전환 검토",
            ),
        )
    if progress >= DEFAULT_GOAL_PROTECTION_PCT:
        return GuardResult(
            guard_name=GUARD_GOAL_PROTECTION,
            status=STATUS_FAIL,
            risk_level=RISK_ORANGE,
            title="목표 근접 구간 — 보호 모드로 전환할 시점입니다.",
            message=(
                f"목표 진행률 {progress:.1f}%로 목표에 매우 근접했습니다. "
                "수익 극대화보다 손실 회피가 우선되는 운영이 어울립니다."
            ),
            evidence=base_evidence,
            watch_next=(
                "drawdown guard 민감도 상향",
                "신규 고위험 추격 진입 제한",
            ),
        )
    if progress >= DEFAULT_GOAL_WARN_PCT:
        return GuardResult(
            guard_name=GUARD_GOAL_PROTECTION,
            status=STATUS_WARN,
            risk_level=RISK_YELLOW,
            title="목표 진행률이 상승 구간 — 무리한 위험 확대 경계.",
            message=(
                f"목표 진행률 {progress:.1f}%로 후반부에 진입했습니다. "
                "추가 위험 확대보다 이익 보호 비중을 키우세요."
            ),
            evidence=base_evidence,
            watch_next=(
                "이벤트 전 과대 포지션 점검",
                "현금 비중 최소치 회복 여부",
            ),
        )

    return GuardResult(
        guard_name=GUARD_GOAL_PROTECTION,
        status=STATUS_PASS,
        risk_level=RISK_GREEN,
        title="목표 진행률이 정상 운영 구간에 있습니다.",
        message=(
            f"목표 진행률 {progress:.1f}%로 기본 운영 모드를 유지할 수 있는 구간입니다."
        ),
        evidence=base_evidence,
    )
