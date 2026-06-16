"""Control Room API schemas — Slice 13.6.

Mirrors the structure of ``frontend/src/mocks/fixtures/controlRoom.fixture.ts``
so the React page can switch between the fixture and the live API
without changing component code.
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
from api.schemas.mission_control import AllocationSlice


class TickerStripItem(CamelModel):
    symbol: str
    price: str
    change: str
    direction: Literal["up", "down", "flat"] = "flat"
    currency: str = "USD"
    logo_url: str | None = None
    held: bool = False


class MarketTapePoint(CamelModel):
    """One sample on the normalized Portfolio / Market Tape series.

    Both values are normalised to a common starting point (typically
    100) so the chart shows relative trajectory — never an absolute
    price prediction. Slice 13.6 cleanup emits these via fixtures
    only; a later slice may attach live data.
    """

    label: str = Field(
        ...,
        description="Bucket label (e.g. T-90, T-60, T-30, T-15, T-0).",
    )
    portfolio: Decimal
    benchmark: Decimal


class MissionProgress(CamelModel):
    current_value: Decimal = Field(default=Decimal("0"))
    target_value: Decimal = Field(default=Decimal("100000000"))
    progress_pct: Decimal = Field(default=Decimal("0"))
    phase: str = Field(default="—")
    early_stop_triggered: bool = False
    goal_mode: str = Field(default="GROWTH")


class StateVectorCell(CamelModel):
    """One real-evidence cell of the operating-state vector.

    The value is sourced from the live regime classification (decision mode,
    confidence, and the rule-derived positive / risk factors) — never a
    fabricated market reading.
    """

    label: str
    value: str
    tone: Literal["info", "warning", "danger", "neutral", "success"] = "neutral"


class OperatingState(CamelModel):
    title: str
    regime: str
    decision_mode: str
    preparation_score: int = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Exposure / preparation score, not a price prediction. "
            "0 = no exposure / fully defensive, 100 = max preparation."
        ),
    )
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    state_vector: list[StateVectorCell] = Field(default_factory=list)


class GuardDriver(CamelModel):
    """One evidence row behind a guard decision (Slice 163 attribution)."""

    label: str
    value: str


class GuardSummaryVM(CamelModel):
    name: str
    status: Literal["PASS", "WARN", "FAIL", "BLOCKED", "INFO"]
    risk_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]
    title: str
    message: str
    # Slice 163: the numbers behind the decision + suggested review actions.
    # Populated in the live Risk Firewall path; empty elsewhere (fixtures,
    # Control Room) so existing visual baselines are unchanged.
    attribution: list[GuardDriver] = Field(default_factory=list)
    watch_next: list[str] = Field(default_factory=list)


class CatalystSummary(CamelModel):
    days_to_event: int | None = None
    title: str
    subtitle: str
    tag: str = "Tentative"
    tone: Literal["info", "warning", "danger", "neutral", "purple"] = "neutral"


class WatchlistItem(CamelModel):
    symbol: str
    label: str
    note: str
    tone: Literal["info", "warning", "danger", "neutral", "success"] = "neutral"


class PortfolioExposureSlice(CamelModel):
    label: str
    weight_pct: Decimal


class ReviewQueueItem(CamelModel):
    title: str
    note: str
    tag: Literal["weekly", "mistake", "thesis", "event"] = "weekly"


class ControlRoomDataState(CamelModel):
    source: Literal["fixture", "live"] = "fixture"
    overview_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    system_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    mission_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    market_tape_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    guard_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    catalyst_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    watchlist_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"
    market_tape_points: int = 0
    guard_count: int = 0
    catalyst_count: int = 0
    watchlist_count: int = 0
    latest_market_at: str | None = None
    latest_event_at: str | None = None
    latest_watchlist_at: str | None = None
    market_freshness_status: Literal["FRESH", "STALE", "MISSING"] = "MISSING"
    catalyst_freshness_status: Literal["FRESH", "STALE", "MISSING"] = "MISSING"
    watchlist_freshness_status: Literal["FRESH", "STALE", "MISSING"] = "MISSING"
    rail_freshness_status: Literal["FRESH", "STALE", "MISSING"] = "MISSING"
    rail_freshness_note: str = ""
    market_stale_after_days: int = 3
    watchlist_stale_after_days: int = 3
    source_note: str
    refresh_note: str


EvidenceNodeKey = Literal["regime", "risk", "events", "portfolio"]
EvidenceNodeTone = Literal["info", "warning", "danger", "neutral", "success"]


class EvidenceNode(CamelModel):
    """One domain node in the cross-tab evidence graph (Slice 167)."""

    key: EvidenceNodeKey
    label: str
    state: str
    tone: EvidenceNodeTone = "info"
    drivers: list[str] = Field(default_factory=list)


class EvidenceLink(CamelModel):
    """A descriptive cross-reference between two evidence nodes."""

    source: EvidenceNodeKey
    target: EvidenceNodeKey
    relation: str


class EvidenceGraph(CamelModel):
    """Regime ↔ Risk ↔ Events ↔ Portfolio evidence, linked (Slice 167).

    Descriptive aggregation of the existing read models — never a directive."""

    nodes: list[EvidenceNode] = Field(default_factory=list)
    links: list[EvidenceLink] = Field(default_factory=list)
    summary: str = ""


class ControlRoomResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    data_state: ControlRoomDataState
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    safety_caption: str = "Global operating posture (not execution)."
    ticker_strip: list[TickerStripItem]
    # Composite technical-posture score (0–100) over the strip universe. Pinned on
    # the left of the strip; descriptive, not a signal. None when no indicators.
    ticker_score: int | None = None
    mission: MissionProgress
    operating_state: OperatingState
    portfolio_exposure: list[PortfolioExposureSlice]
    # Per-ticker allocation (sectors are unpopulated, so the sector exposure above
    # is all "Unclassified") — used for the holdings composition pie.
    allocation: list[AllocationSlice] = Field(default_factory=list)
    review_queue: list[ReviewQueueItem]
    interpretation_cards: list[str]
    risk_firewall: list[GuardSummaryVM]
    catalyst_watch: list[CatalystSummary]
    watchlist: list[WatchlistItem]
    market_tape: list[MarketTapePoint] = Field(default_factory=list)
    # Slice 167: cross-tab evidence graph (live only; None in fixtures).
    evidence_graph: EvidenceGraph | None = None
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "CatalystSummary",
    "ControlRoomDataState",
    "ControlRoomResponse",
    "EvidenceGraph",
    "EvidenceLink",
    "EvidenceNode",
    "GuardDriver",
    "GuardSummaryVM",
    "MarketTapePoint",
    "MissionProgress",
    "OperatingState",
    "PortfolioExposureSlice",
    "ReviewQueueItem",
    "TickerStripItem",
    "WatchlistItem",
]
