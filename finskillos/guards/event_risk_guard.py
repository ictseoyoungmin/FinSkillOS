"""Event Risk Guard — live Catalyst Watch exposure (Slice 89).

Slices 10–11 populate the ``events`` / ``news`` tables and add the
``EventRiskService`` deterministic scorer. ``RiskGuardService`` now feeds a
``EventRiskSummary`` into the guard ladder, so this guard reports the live
upcoming-catalyst exposure instead of static deferred copy.

It stays **INFO-only** by design: event exposure is descriptive context for the
Risk Firewall, not a buy/sell signal, and it must not change the WARN/FAIL
ladder's overall status. When no event context is supplied (``event_risk`` is
``None`` / ``connected=False``) it keeps the existing guard id but describes the
missing Catalyst Watch evidence directly so direct callers stay back-compatible.
"""

from __future__ import annotations

from finskillos.guards.base import (
    GUARD_EVENT_PLACEHOLDER,
    RISK_GREEN,
    STATUS_INFO,
    GuardInput,
    GuardResult,
)


def evaluate(inputs: GuardInput) -> GuardResult:
    summary = inputs.event_risk
    if summary is None or not summary.connected:
        return _deferred_result()
    if summary.upcoming_count <= 0:
        return _no_events_result()
    return _connected_result(summary)


def _deferred_result() -> GuardResult:
    return GuardResult(
        guard_name=GUARD_EVENT_PLACEHOLDER,
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="Catalyst Watch 이벤트 근거가 아직 없습니다.",
        message=(
            "이벤트 노출도 평가는 Catalyst Watch의 예정 이벤트와 보유 종목 연결 "
            "근거가 있을 때 서술적 참고 지표로 표시됩니다."
        ),
        evidence={
            "events_table_connected": False,
            "event_exposure_status": "missing_catalyst_watch_evidence",
        },
        watch_next=(
            "Catalyst Watch 이벤트 시드 또는 refresh 이후 이벤트 노출도 재평가",
        ),
    )


def _no_events_result() -> GuardResult:
    return GuardResult(
        guard_name=GUARD_EVENT_PLACEHOLDER,
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="추적 중인 예정 이벤트가 없습니다.",
        message=(
            "Catalyst Watch에 등록된 다가오는 이벤트가 없어 이벤트 노출도는 현재 "
            "중립입니다. System Ops 이벤트 시드 이후 다시 평가됩니다."
        ),
        evidence={
            "events_table_connected": True,
            "upcoming_count": 0,
        },
        watch_next=(
            "Catalyst Watch에 다가오는 이벤트가 등록되면 노출도를 자동 갱신",
        ),
    )


def _connected_result(summary) -> GuardResult:
    affected = ", ".join(summary.affected_tickers) if summary.affected_tickers else "—"
    return GuardResult(
        guard_name=GUARD_EVENT_PLACEHOLDER,
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title=(
            f"예정 이벤트 {summary.upcoming_count}건 모니터링 중 "
            f"(최고 노출 {summary.highest_label})."
        ),
        message=(
            "Catalyst Watch 노출도는 보유 종목과 이벤트 연결을 바탕으로 한 서술적 "
            "참고 지표입니다. 가격 방향 예측이 아니라 점검이 필요한 노출 구간을 "
            "표시합니다."
        ),
        evidence={
            "events_table_connected": True,
            "upcoming_count": summary.upcoming_count,
            "holdings_relevant_count": summary.holdings_relevant_count,
            "highest_label": summary.highest_label,
            "highest_score": summary.highest_score,
            "nearest_days": summary.nearest_days,
            "affected_tickers": affected,
        },
        watch_next=(
            "보유 종목과 연결된 고노출 이벤트의 일정/상태를 Catalyst Watch에서 확인",
        ),
    )
