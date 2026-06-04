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


class PortfolioReconciliation(CamelModel):
    """Coherence check: does the snapshot total equal positions + cash? (Slice 157)"""

    status: Literal["OK", "MISMATCH", "NO_BASELINE"] = "NO_BASELINE"
    snapshot_total: Decimal = Field(default=Decimal("0"))
    positions_value: Decimal = Field(default=Decimal("0"))
    cash_value: Decimal = Field(default=Decimal("0"))
    reconciled_total: Decimal = Field(default=Decimal("0"))
    drift: Decimal = Field(default=Decimal("0"))
    drift_pct: Decimal = Field(default=Decimal("0"))
    detail: str = "No portfolio snapshot baseline exists yet."


class PortfolioConstraint(CamelModel):
    """One portfolio constraint with its headroom state (Slice 166).

    Descriptive constraint status — headroom against a stored risk policy, never
    a directive to trade."""

    label: str
    status: Literal["OK", "WATCH", "BREACH", "UNKNOWN"] = "OK"
    detail: str = ""


class PositionRow(CamelModel):
    """One editable holding (Slice 158)."""

    id: str
    ticker: str
    quantity: Decimal
    market_value: Decimal
    average_cost: Decimal | None = None
    pnl_pct: Decimal | None = None
    sector: str | None = None
    theme: str | None = None
    strategy_type: str = "swing"
    thesis: str | None = None


class PositionInput(CamelModel):
    """Create/update payload for a holding."""

    ticker: str = Field(..., min_length=1, max_length=32)
    quantity: Decimal
    market_value: Decimal
    average_cost: Decimal | None = None
    sector: str | None = Field(default=None, max_length=80)
    theme: str | None = Field(default=None, max_length=80)
    strategy_type: str = Field(default="swing", max_length=40)
    thesis: str | None = None


class SnapshotBaselineInput(CamelModel):
    """Edit the stored snapshot baseline (the account's official value)."""

    total_value: Decimal | None = None
    cash_value: Decimal | None = None


class PortfolioImportRequest(CamelModel):
    """CSV text submitted for a portfolio import (Slice 159)."""

    csv_text: str = Field(..., min_length=0, max_length=200_000)


class PortfolioImportRow(CamelModel):
    """One parsed row in the import preview, tagged ADD vs UPDATE."""

    ticker: str
    quantity: Decimal
    market_value: Decimal
    action: Literal["ADD", "UPDATE"]


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
    reconciliation: PortfolioReconciliation = Field(
        default_factory=PortfolioReconciliation
    )
    positions: list[PositionRow] = Field(default_factory=list)
    constraints: list[PortfolioConstraint] = Field(default_factory=list)
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


class PortfolioImportResult(CamelModel):
    """Dry-run preview (and, on confirm, applied) result of a CSV import.

    Upsert semantics only — tickers absent from the CSV are left untouched.
    """

    status: Literal["PREVIEW", "APPLIED", "ERROR"]
    adds: int = 0
    updates: int = 0
    total_rows: int = 0
    parse_errors: list[str] = Field(default_factory=list)
    rows: list[PortfolioImportRow] = Field(default_factory=list)
    detail: str = ""
    # Populated only when status == "APPLIED" so the client can refresh in place.
    snapshot: MissionControlResponse | None = None


__all__ = [
    "CapitalMapSlice",
    "PortfolioReconciliation",
    "PortfolioConstraint",
    "PositionRow",
    "PositionInput",
    "SnapshotBaselineInput",
    "PortfolioImportRequest",
    "PortfolioImportRow",
    "PortfolioImportResult",
    "GoalTracker",
    "MilestoneItem",
    "MilestoneState",
    "MissionControlResponse",
    "PortfolioSnapshotPanel",
]
