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


class TickerStripItem(CamelModel):
    symbol: str
    price: str
    change: str
    direction: Literal["up", "down", "flat"] = "flat"


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


class GuardSummaryVM(CamelModel):
    name: str
    status: Literal["PASS", "WARN", "FAIL", "BLOCKED", "INFO"]
    risk_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "UNKNOWN"]
    title: str
    message: str


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


class ControlRoomResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    interpretation: IntegratedInterpretation
    watchpoints: list[EvidenceWatchpoint]
    safety_caption: str = "Global operating posture (not execution)."
    ticker_strip: list[TickerStripItem]
    mission: MissionProgress
    operating_state: OperatingState
    portfolio_exposure: list[PortfolioExposureSlice]
    review_queue: list[ReviewQueueItem]
    interpretation_cards: list[str]
    risk_firewall: list[GuardSummaryVM]
    catalyst_watch: list[CatalystSummary]
    watchlist: list[WatchlistItem]
    market_tape: list[MarketTapePoint] = Field(default_factory=list)
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "CatalystSummary",
    "ControlRoomResponse",
    "GuardSummaryVM",
    "MarketTapePoint",
    "MissionProgress",
    "OperatingState",
    "PortfolioExposureSlice",
    "ReviewQueueItem",
    "TickerStripItem",
    "WatchlistItem",
]
