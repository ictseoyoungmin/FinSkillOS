"""Mission Control fixture — Slice 13.8.

Deterministic payload for ``GET /api/mission-control``. Mirrors the
v4.1 mockup ``page-mission`` section: goal tracker hero + milestone
timeline + capital map. Numbers line up with the Control Room
fixture so the two pages tell the same story.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP, D
from api.schemas.common import SystemStatus
from api.schemas.mission_control import (
    CapitalMapSlice,
    GoalTracker,
    MilestoneItem,
    MissionControlResponse,
    PortfolioSnapshotPanel,
)


def mission_control_fixture() -> MissionControlResponse:
    return MissionControlResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=3),
        goal=GoalTracker(
            current_value=D("73420000"),
            target_value=D("100000000"),
            remaining_value=D("26580000"),
            progress_pct=D("73.4"),
            progress_ratio=D("0.734"),
            goal_mode="BALANCED",
            early_stop_triggered=False,
            phase="Phase 3 / 5",
            challenge_label="1억 KRW challenge",
        ),
        milestones=[
            MilestoneItem(pct=25, label="Foundation", state="COMPLETED"),
            MilestoneItem(pct=50, label="Acceleration", state="COMPLETED"),
            MilestoneItem(pct=75, label="Approaching", state="APPROACHING"),
            MilestoneItem(pct=100, label="Challenge Complete", state="PENDING"),
        ],
        portfolio=PortfolioSnapshotPanel(
            total_value=D("73420000"),
            cash_value=D("9200000"),
            position_count=4,
            largest_position_ticker="TSLA",
            largest_position_weight_pct=D("13.8"),
            over_single_limit_tickers=["TSLA"],
        ),
        capital_map=[
            CapitalMapSlice(label="AI / Semis", weight_pct=D("31.4"), tone="warning"),
            CapitalMapSlice(label="Mega Cap Tech", weight_pct=D("24.8"), tone="info"),
            CapitalMapSlice(label="EV / Robotaxi", weight_pct=D("13.8"), tone="warning"),
            CapitalMapSlice(label="Space / Launch", weight_pct=D("9.1"), tone="info"),
            CapitalMapSlice(label="Cash", weight_pct=D("12.5"), tone="neutral"),
            CapitalMapSlice(label="Other", weight_pct=D("8.4"), tone="neutral"),
        ],
        theme_map=[
            CapitalMapSlice(label="AI Infrastructure", weight_pct=D("28.2"), tone="warning"),
            CapitalMapSlice(label="Robotaxi", weight_pct=D("13.8"), tone="warning"),
            CapitalMapSlice(label="Cloud / SaaS", weight_pct=D("14.6"), tone="info"),
            CapitalMapSlice(label="Macro Hedge", weight_pct=D("5.4"), tone="info"),
        ],
        challenge_status_caption=(
            "1억 KRW challenge active · 73.4% progress · "
            "challenge complete + early-stop state remain pending."
        ),
    )


__all__ = ["mission_control_fixture"]
