"""Market Kernel fixture — Slice 13.7.

Deterministic payload for ``GET /api/market-kernel?ticker=…``. Mirrors
the existing Streamlit Market Kernel: symbol universe rail, header,
chart bars, indicator snapshot, and an event overlay summary that
re-uses the same NVDA / FOMC catalysts the Control Room fixture
shows.
"""

from __future__ import annotations

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.fixtures._focus_tickers import FOCUS_TICKERS, FocusTicker
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import (
    EventOverlayItem,
    IndicatorSnapshot,
    MarketBarPoint,
    MarketKernelHeader,
    MarketKernelResponse,
    UniverseTicker,
)

MARKET_KERNEL_DEFAULT_TICKER = "NVDA"

# Left-rail universe — Slice-04 default focus universe + the two macro
# proxies the Streamlit page already surfaces.
_UNIVERSE: tuple[UniverseTicker, ...] = (
    UniverseTicker(symbol="NVDA", label="NVIDIA", kind="FOCUS"),
    UniverseTicker(symbol="TSLA", label="Tesla", kind="FOCUS"),
    UniverseTicker(symbol="AAPL", label="Apple", kind="FOCUS"),
    UniverseTicker(symbol="MSFT", label="Microsoft", kind="FOCUS"),
    UniverseTicker(symbol="SMH", label="Semiconductor ETF", kind="SECTOR_ETF"),
    UniverseTicker(symbol="SPY", label="S&P 500 ETF", kind="INDEX_ETF"),
    UniverseTicker(symbol="QQQ", label="Nasdaq 100 ETF", kind="INDEX_ETF"),
    UniverseTicker(symbol="VIX", label="Volatility Proxy", kind="MACRO_PROXY"),
    UniverseTicker(symbol="DXY", label="USD Index Proxy", kind="MACRO_PROXY"),
    UniverseTicker(symbol="US10Y", label="10Y Yield Proxy", kind="MACRO_PROXY"),
)

SUPPORTED_FOCUS_TICKERS = tuple(FOCUS_TICKERS.keys())


def market_kernel_fixture(ticker: str | None = None) -> MarketKernelResponse:
    """Build the Market Kernel response for ``ticker`` (uppercased)."""

    resolved, focus = _resolve_focus(ticker)

    if focus is None:
        return _missing_payload(resolved)

    return MarketKernelResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=judgment(
            "TECHNICAL SIGNAL JUDGMENT",
            "Constructive Tape",
            "with Overheat Risk",
            (
                f"{focus.symbol} keeps a constructive trend stack while "
                "momentum and event proximity make the signal conditional."
            ),
            68,
        ),
        drivers=drivers(
            (str(focus.indicators.rsi_14), "RSI(14)", "Elevated momentum requires context."),
            (
                focus.indicators.trend_state or "UNKNOWN",
                "Trend state",
                "Stored indicator snapshot remains constructive.",
            ),
            (
                str(len(focus.events)),
                "Linked events",
                "Catalyst overlays are part of the interpretation.",
            ),
        ),
        conflicts=conflicts(
            ("Trend support vs overheat", "EMA alignment is constructive while RSI is elevated."),
            (
                "Stored bars vs live tape",
                "The fixture snapshot is deterministic and not a live feed.",
            ),
        ),
        integrated_interpretation=interpretation(
            "Technical signal is constructive but constrained by overheat risk.",
            "The view separates chart evidence, indicator state, and event "
            "overlays before forming context.",
            "Fresh market bars or event updates may alter the confidence level.",
        ),
        review_watchpoints=watchpoints(
            ("RSI cooldown", "Watch whether momentum normalizes without breaking the trend stack."),
            ("Event proximity", "Recheck overlays when event timing or linked news changes."),
        ),
        universe=list(_UNIVERSE),
        header=MarketKernelHeader(
            ticker=focus.symbol,
            label=focus.label,
            timeframe="1d",
            latest_close=focus.bars[-1].close,
            latest_time=focus.bars[-1].bar_time,
            data_status="OK",
        ),
        bars=[
            MarketBarPoint(
                bar_time=bar.bar_time,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in focus.bars
        ],
        indicators=IndicatorSnapshot(
            rsi_14=focus.indicators.rsi_14,
            ema_20=focus.indicators.ema_20,
            ema_60=focus.indicators.ema_60,
            ema_120=focus.indicators.ema_120,
            bb_position=focus.indicators.bb_position,
            volume_z_score=focus.indicators.volume_z_score,
            momentum_score=focus.indicators.momentum_score,
            trend_state=focus.indicators.trend_state,
        ),
        events=[EventOverlayItem(**event) for event in focus.events],
        watchpoints=list(focus.watchpoints),
        interpretation=focus.interpretation,
        setup_hint=None,
        safety_caption=(
            "Technical interpretation (not entry signal). Stored data only · not prediction."
        ),
    )


def _resolve_focus(ticker: str | None) -> tuple[str, FocusTicker | None]:
    normalised = (ticker or MARKET_KERNEL_DEFAULT_TICKER).strip().upper()
    if not normalised:
        normalised = MARKET_KERNEL_DEFAULT_TICKER
    return normalised, FOCUS_TICKERS.get(normalised)


def _missing_payload(ticker: str) -> MarketKernelResponse:
    return MarketKernelResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=judgment(
            "TECHNICAL SIGNAL JUDGMENT",
            "Data Missing",
            "for Selected Symbol",
            f"{ticker} has no stored technical snapshot in the fixture set.",
            30,
        ),
        drivers=drivers(
            ("0", "Stored bars", "No local bar series is available."),
            ("MISSING", "Data status", "The page can only show setup guidance."),
            ("0", "Linked events", "No event overlay is attached to this symbol."),
        ),
        conflicts=conflicts(
            (
                "Selected symbol vs fixture scope",
                "The requested ticker is outside the deterministic fixture universe.",
            ),
        ),
        integrated_interpretation=interpretation(
            "No technical judgment is available for the selected ticker.",
            "This prevents the UI from inventing signal context when source data is missing.",
            "A supported ticker or future stored snapshot is required.",
        ),
        review_watchpoints=watchpoints(
            ("Fixture coverage", "Select a left-rail ticker with stored bars."),
        ),
        universe=list(_UNIVERSE),
        header=MarketKernelHeader(
            ticker=ticker,
            label=ticker,
            timeframe="1d",
            latest_close=None,
            latest_time=None,
            data_status="MISSING",
        ),
        bars=[],
        indicators=IndicatorSnapshot(),
        events=[],
        watchpoints=[
            f"No stored market bar or indicator snapshot exists for {ticker}.",
        ],
        interpretation=(
            f"{ticker} has no stored market bars or indicator snapshots in "
            "the v0 fixture set. Select a focus ticker from the left rail."
        ),
        setup_hint=(
            f"{ticker} is not in the Slice 13.7 fixture set. "
            f"Supported tickers: {', '.join(SUPPORTED_FOCUS_TICKERS)}."
        ),
        safety_caption=(
            "Technical interpretation (not entry signal). Stored data only · not prediction."
        ),
    )


__all__ = [
    "MARKET_KERNEL_DEFAULT_TICKER",
    "SUPPORTED_FOCUS_TICKERS",
    "market_kernel_fixture",
]
