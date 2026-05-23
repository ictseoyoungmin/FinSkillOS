"""Mission Control API schemas — Slice 13.8.

Camel-case Pydantic shape for ``GET /api/mission-control``. The
payload wraps the Slice-03 goal tracker (current / target / progress)
+ the PortfolioService snapshot read model (cash, positions, sector
exposure). Descriptive only — never emits trade directives.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.common import (
    CamelModel,
    EvidenceConflict,
    EvidenceDriver,
    EvidenceWatchpoint,
    IntegratedInterpretation,
    JudgmentHeader,
    SystemStatus,
)

MilestoneState = Literal["PENDING", "APPROACHING", "COMPLETED"]


class GoalTracker(CamelModel):
    """Hero card numbers shown at the top of Mission Control."""

    current_value: Decimal
    target_value: Decimal
    remaining_value: Decimal
    progress_pct: Decimal = Field(..., ge=0, le=100)
    progress_ratio: Decimal = Field(..., ge=0, le=1)
    goal_mode: str = Field(
        ...,
        description=(
            "One of GROWTH / BALANCED / PROTECTION / COMPLETION_GUARD / "
            "CHALLENGE_COMPLETE — see finskillos.goal.goal_tracker."
        ),
    )
    early_stop_triggered: bool = False
    phase: str = Field(default="—")
    challenge_label: str = Field(
        default="1억 KRW challenge",
        description="User-facing copy of the active challenge.",
    )


class MilestoneItem(CamelModel):
    """One row of the 25 / 50 / 75 / 100% milestone timeline."""

    pct: int = Field(..., ge=0, le=100)
    label: str
    state: MilestoneState


class PortfolioSnapshotPanel(CamelModel):
    """Compact stats shown next to the goal tracker."""

    total_value: Decimal
    cash_value: Decimal
    position_count: int = Field(..., ge=0)
    largest_position_ticker: str | None = None
    largest_position_weight_pct: Decimal = Field(default=Decimal("0"))
    over_single_limit_tickers: list[str] = Field(default_factory=list)


class CapitalMapSlice(CamelModel):
    """One entry in the sector / theme exposure map."""

    label: str
    weight_pct: Decimal
    tone: Literal["info", "warning", "danger", "neutral", "success"] = "info"


class MissionControlResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    goal: GoalTracker
    milestones: list[MilestoneItem]
    portfolio: PortfolioSnapshotPanel
    capital_map: list[CapitalMapSlice]
    theme_map: list[CapitalMapSlice] = Field(default_factory=list)
    challenge_status_caption: str = Field(
        default=(
            "Challenge active · descriptive view only · "
            "no execution controls."
        ),
    )
    safety_caption: str = "Read mode — Goal interpretation (not return forecast)."
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "CapitalMapSlice",
    "GoalTracker",
    "MilestoneItem",
    "MilestoneState",
    "MissionControlResponse",
    "PortfolioSnapshotPanel",
]
