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


class QuantLabFeatureCoverage(CamelModel):
    name: str
    bars: int
    pct: float


class QuantLabCoverage(CamelModel):
    """What data fed the backtest — date span + per-feature bar coverage."""

    date_start: str = ""
    date_end: str = ""
    bar_count: int = 0
    features: list[QuantLabFeatureCoverage] = Field(default_factory=list)


class QuantLabWindow(CamelModel):
    index: int
    date_start: str
    date_end: str
    bar_count: int
    total_return: float | None = None
    sharpe: float | None = None
    exposure_pct: float = 0.0
    round_trips: int = 0


class QuantLabDataState(CamelModel):
    source: str = "live"
    ticker: str = ""
    bar_count: int = Field(default=0, ge=0)
    regime_covered: bool = False
    data_note: str = ""


class QuantLabScreenRow(CamelModel):
    ticker: str
    bar_count: int
    total_return: float | None = None
    sharpe: float | None = None
    max_drawdown: float | None = None
    exposure_pct: float = 0.0
    round_trips: int = 0


class QuantLabScreenResponse(CamelModel):
    """Run one strategy across many tickers, ranked — a multi-asset screen."""

    generated_at: str
    system_status: SystemStatus
    strategy_name: str
    source: str = "live"
    rows: list[QuantLabScreenRow] = Field(default_factory=list)
    safety_caption: str = ""


class QuantLabSavedSummary(CamelModel):
    id: str
    name: str
    ticker: str
    created_at: str


class QuantLabSavedList(CamelModel):
    specs: list[QuantLabSavedSummary] = Field(default_factory=list)


class QuantLabPortfolioPoint(CamelModel):
    date: str
    strategy: float
    benchmark: float
    exposure: float = 0.0  # fraction of sleeves in-market [0..1]


class QuantLabPortfolioResponse(CamelModel):
    """Equal-weight multi-asset portfolio synthesis — one combined capital curve."""

    generated_at: str
    system_status: SystemStatus
    strategy_name: str
    source: str = "live"
    tickers: list[str] = Field(default_factory=list)
    weight: float = 0.0
    curve: list[QuantLabPortfolioPoint] = Field(default_factory=list)
    metrics: QuantLabMetrics = Field(default_factory=QuantLabMetrics)
    safety_caption: str = ""


class QuantLabRunRequest(CamelModel):
    """An agent-authored free-form strategy to backtest (Phase 21.8).

    ``entry`` / ``exit`` are condition trees (see finskillos.simulation.spec_json)."""

    ticker: str
    entry: dict
    exit_: dict = Field(alias="exit")
    name: str | None = None
    description: str | None = None
    timeframe: str = "1d"


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
    coverage: QuantLabCoverage = Field(default_factory=QuantLabCoverage)
    walk_forward: list[QuantLabWindow] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
