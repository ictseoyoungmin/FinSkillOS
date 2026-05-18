"""Event Risk Guard — placeholder for Slice 11 Event Radar integration.

Slice 06 does not yet ingest events / earnings / FOMC dates; the
``events`` and ``news`` tables remain empty until Slices 10–11. This
guard exists so the Risk Firewall ladder is complete and so the
orchestrator can light up an INFO badge that says "event-driven risk
will be tracked here once the data is connected." It NEVER raises
WARN/FAIL on its own.
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
    return GuardResult(
        guard_name=GUARD_EVENT_PLACEHOLDER,
        status=STATUS_INFO,
        risk_level=RISK_GREEN,
        title="이벤트 위험 평가는 이후 슬라이스에서 연결됩니다.",
        message=(
            "Event Radar 슬라이스가 events / news 테이블을 채우면 이벤트 노출도, "
            "기대감 선반영, sell-the-news 위험을 자동으로 점검합니다."
        ),
        evidence={
            "events_table_connected": False,
            "deferred_to": "Slice 11 Event Radar",
        },
        watch_next=(
            "Slice 10 News Intelligence / Slice 11 Event Radar 진행 후 재평가",
        ),
    )
