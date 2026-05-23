"""Market Kernel API schemas — Slice 13.7.

Camel-case Pydantic shape for ``GET /api/market-kernel?ticker=…``.
The payload wraps the same data the Streamlit Market Kernel surfaces
(stored bars + indicator snapshot + event overlay summary) without
ever emitting buy / sell directives.

Field policy:
  * All numeric inputs are ``Numeric = Decimal | None`` so missing
    snapshots stay representable.
  * Chart points are normalised to a single ``LineChartPoint`` shape so
    React can reuse the same primitive in Control Room and Market
    Kernel.
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


class UniverseTicker(CamelModel):
    """One ticker entry shown in the left-rail symbol universe."""

    symbol: str
    label: str
    kind: Literal["FOCUS", "INDEX_ETF", "SECTOR_ETF", "MACRO_PROXY"] = "FOCUS"


class MarketBarPoint(CamelModel):
    """One historical OHLCV point for the chart panel.

    ``open`` / ``high`` / ``low`` are nullable because macro proxies
    (VIX, DXY, US10Y) sometimes only report a close.
    """

    bar_time: str = Field(..., description="ISO-8601 timestamp.")
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal
    volume: Decimal | None = None


class IndicatorSnapshot(CamelModel):
    """Latest indicator snapshot for the selected symbol."""

    rsi_14: Decimal | None = None
    ema_20: Decimal | None = None
    ema_60: Decimal | None = None
    ema_120: Decimal | None = None
    bb_position: Decimal | None = None
    volume_z_score: Decimal | None = None
    momentum_score: Decimal | None = None
    trend_state: str | None = None


class EventOverlayItem(CamelModel):
    days_to_event: int | None = None
    title: str
    subtitle: str = ""
    tag: str = "Tentative"
    tone: Literal["info", "warning", "danger", "neutral", "purple"] = "neutral"


class MarketKernelHeader(CamelModel):
    ticker: str
    label: str
    timeframe: str
    latest_close: Decimal | None = None
    latest_time: str | None = None
    data_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"


class MarketKernelResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    drivers: list[EvidenceDriver]
    conflicts: list[EvidenceConflict]
    integrated_interpretation: IntegratedInterpretation
    review_watchpoints: list[EvidenceWatchpoint]
    universe: list[UniverseTicker]
    header: MarketKernelHeader
    bars: list[MarketBarPoint]
    indicators: IndicatorSnapshot
    events: list[EventOverlayItem]
    watchpoints: list[str] = Field(default_factory=list)
    interpretation: str = ""
    setup_hint: str | None = None
    safety_caption: str = (
        "Technical interpretation (not entry signal). Stored data only · "
        "not prediction."
    )
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "EventOverlayItem",
    "IndicatorSnapshot",
    "MarketBarPoint",
    "MarketKernelHeader",
    "MarketKernelResponse",
    "UniverseTicker",
]
