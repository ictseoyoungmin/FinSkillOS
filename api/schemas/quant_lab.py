"""Quant Lab read-model schemas (Phase 21.2).

Descriptive simulation output: an equity curve vs a buy-and-hold benchmark,
simulated *exposure* windows (ON/OFF, never buy/sell), and the absorbed METRIC
rulebook stats. Every payload carries a not-advice safety caption.
"""

from __future__ import annotations

from pydantic import Field

from api.schemas.common import CamelModel, JudgmentHeader, SystemStatus


class QuantLabStrategyOption(CamelModel):
    id: str
    name: str
    description: str


class QuantLabStrategySummary(CamelModel):
    id: str
    name: str
    description: str
    ticker: str
    entry_text: str
    exit_text: str


class QuantLabEquityPoint(CamelModel):
    date: str
    strategy: float
    benchmark: float
    exposure: bool = False
    close: float = 0.0
    regime: str | None = None


class QuantLabSegment(CamelModel):
    start: str
    end: str


class QuantLabMarker(CamelModel):
    date: str
    kind: str  # "ENTER" (노출 시작) | "EXIT" (노출 해제) — never buy/sell
    price: float


class QuantLabMetrics(CamelModel):
    total_return: float | None = None
    cagr: float | None = None
    annual_volatility: float | None = None
    sharpe: float | None = None
    sortino: float | None = None
    max_drawdown: float | None = None
    calmar: float | None = None
    exposure_pct: float = 0.0
    round_trips: int = 0
    win_rate: float | None = None


class QuantLabDataState(CamelModel):
    source: str = "live"
    ticker: str = ""
    bar_count: int = Field(default=0, ge=0)
    regime_covered: bool = False
    data_note: str = ""


class QuantLabResponse(CamelModel):
    generated_at: str
    system_status: SystemStatus
    judgment: JudgmentHeader
    strategy: QuantLabStrategySummary
    metrics: QuantLabMetrics
    equity_curve: list[QuantLabEquityPoint] = Field(default_factory=list)
    exposure_segments: list[QuantLabSegment] = Field(default_factory=list)
    markers: list[QuantLabMarker] = Field(default_factory=list)
    available_strategies: list[QuantLabStrategyOption] = Field(default_factory=list)
    available_tickers: list[str] = Field(default_factory=list)
    safety_caption: str = ""
    data_state: QuantLabDataState = Field(default_factory=QuantLabDataState)
    warnings: list[str] = Field(default_factory=list)
