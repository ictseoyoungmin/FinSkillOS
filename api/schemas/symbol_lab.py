"""Symbol Lab API schemas — Slice 13.7.

Camel-case Pydantic shape for ``GET /api/symbol-lab?ticker=…``. Wraps
the existing ``SymbolLabViewModel`` so the React page can render the
position context / technical snapshot / recent bars / alerts / news /
watchpoints without re-implementing any indicator or regime logic.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import Field

from api.schemas.analysis_workspace import RegimeContext
from api.schemas.common import CamelModel, SystemStatus
from api.schemas.market_kernel import IndicatorSnapshot


class SymbolPosition(CamelModel):
    ticker: str
    sector: str | None = None
    theme: str | None = None
    strategy_type: str | None = None
    market_value: Decimal | None = None
    portfolio_weight: Decimal | None = None
    pnl_pct: Decimal | None = None
    quantity: Decimal | None = None
    thesis: str | None = None
    over_single_position_limit: bool = False


class SymbolRecentBar(CamelModel):
    bar_time: str
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    close: Decimal
    volume: Decimal | None = None


class SymbolAlert(CamelModel):
    guard_name: str
    severity: str
    title: str
    message: str = ""
    alert_date: date


class SymbolNewsItem(CamelModel):
    title: str
    source: str
    published_at: str
    sentiment_label: str = "UNKNOWN"
    impact_score: Decimal = Decimal("0")
    risk_note: str | None = None
    url: str = ""


class SymbolLabHeader(CamelModel):
    ticker: str
    timeframe: str
    latest_close: Decimal | None = None
    latest_time: str | None = None
    data_status: Literal["OK", "PARTIAL", "MISSING"] = "MISSING"


class SymbolLabResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    header: SymbolLabHeader
    technical: IndicatorSnapshot
    recent_bars: list[SymbolRecentBar] = Field(default_factory=list)
    position: SymbolPosition | None = None
    alerts: list[SymbolAlert] = Field(default_factory=list)
    news: list[SymbolNewsItem] = Field(default_factory=list)
    regime: RegimeContext | None = None
    watchpoints: list[str] = Field(default_factory=list)
    interpretation: str = ""
    setup_hint: str | None = None
    safety_caption: str = "Stored data only · not prediction · no execution"
    source: Literal["fixture", "live"] = "fixture"


__all__ = [
    "SymbolAlert",
    "SymbolLabHeader",
    "SymbolLabResponse",
    "SymbolNewsItem",
    "SymbolPosition",
    "SymbolRecentBar",
]
