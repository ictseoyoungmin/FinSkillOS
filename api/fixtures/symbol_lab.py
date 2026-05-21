"""Symbol Lab fixture — Slice 13.7.

Deterministic payload for ``GET /api/symbol-lab?ticker=…``. Mirrors
``SymbolLabViewModel``: header + technical snapshot + recent bars +
position context + alerts + news + regime + watchpoints.

Default ticker resolution (matches the Streamlit page):
    user input → first held position (TSLA in fixture) → "TSLA"
"""

from __future__ import annotations

from datetime import date

from api.fixtures._common import FIXTURE_TIMESTAMP, D
from api.fixtures._focus_tickers import FOCUS_TICKERS, FocusTicker
from api.fixtures.analysis_workspace import _regime_context
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import IndicatorSnapshot
from api.schemas.symbol_lab import (
    SymbolAlert,
    SymbolLabHeader,
    SymbolLabResponse,
    SymbolNewsItem,
    SymbolPosition,
    SymbolRecentBar,
)

SYMBOL_LAB_DEFAULT_TICKER = "TSLA"


# Position fixtures keyed by ticker — only TSLA is currently held in
# the v0 fixture set, matching the Control Room "Single Position
# Limit" guard message.
_POSITIONS: dict[str, SymbolPosition] = {
    "TSLA": SymbolPosition(
        ticker="TSLA",
        sector="Consumer Discretionary",
        theme="EV / Robotaxi",
        strategy_type="CORE_HOLDING",
        market_value=D("12_400_000"),
        portfolio_weight=D("0.1690"),
        pnl_pct=D("8.40"),
        quantity=D("50"),
        thesis=(
            "Long-term EV / robotaxi exposure. Single-position size is "
            "above the configured review threshold; size scaling is on "
            "watch, not a directive."
        ),
        over_single_position_limit=True,
    ),
}


_ALERTS: dict[str, tuple[SymbolAlert, ...]] = {
    "TSLA": (
        SymbolAlert(
            guard_name="SINGLE_POSITION_LIMIT_GUARD",
            severity="WARN",
            title="Single Position Limit",
            message="TSLA exceeds configured ₩10M review threshold.",
            alert_date=date(2026, 5, 19),
        ),
    ),
}


_NEWS: dict[str, tuple[SymbolNewsItem, ...]] = {
    "NVDA": (
        SymbolNewsItem(
            title="NVIDIA prepares Q1 print; AI demand commentary in focus",
            source="MockWire",
            published_at="2026-05-19T13:30:00+00:00",
            sentiment_label="POSITIVE",
            impact_score=D("0.72"),
            risk_note="Earnings inside the catalyst window; expect headline volatility.",
            url="https://example.com/news/nvda-q1-preview",
        ),
        SymbolNewsItem(
            title="Hyperscaler data-center capex remains supportive — analyst note",
            source="MockWire",
            published_at="2026-05-18T15:00:00+00:00",
            sentiment_label="POSITIVE",
            impact_score=D("0.54"),
            risk_note=None,
            url="https://example.com/news/datacenter-capex",
        ),
    ),
    "TSLA": (
        SymbolNewsItem(
            title="Robotaxi pilot expansion: descriptive overview",
            source="MockWire",
            published_at="2026-05-18T18:00:00+00:00",
            sentiment_label="NEUTRAL",
            impact_score=D("0.42"),
            risk_note="Headline risk — descriptive, not directive.",
            url="https://example.com/news/tsla-robotaxi-overview",
        ),
        SymbolNewsItem(
            title="EV credit policy update tracked by sector media",
            source="MockWire",
            published_at="2026-05-17T11:00:00+00:00",
            sentiment_label="MIXED",
            impact_score=D("0.31"),
            risk_note=None,
            url="https://example.com/news/ev-policy-update",
        ),
    ),
    "AAPL": (
        SymbolNewsItem(
            title="Services momentum cited in mega-cap commentary",
            source="MockWire",
            published_at="2026-05-19T08:00:00+00:00",
            sentiment_label="POSITIVE",
            impact_score=D("0.48"),
            risk_note=None,
            url="https://example.com/news/aapl-services",
        ),
    ),
}


def symbol_lab_fixture(ticker: str | None = None) -> SymbolLabResponse:
    """Build the Symbol Lab response for ``ticker`` (uppercased)."""

    resolved, focus = _resolve_focus(ticker)

    if focus is None:
        return _missing_payload(resolved)

    position = _POSITIONS.get(resolved)
    alerts = _ALERTS.get(resolved, ())
    news = _NEWS.get(resolved, ())

    return SymbolLabResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(
            db="LIVE",
            mode="READ_MODE",
            guard_count=len(alerts),
        ),
        header=SymbolLabHeader(
            ticker=focus.symbol,
            timeframe="1d",
            latest_close=focus.bars[-1].close,
            latest_time=focus.bars[-1].bar_time,
            data_status="OK",
        ),
        technical=IndicatorSnapshot(
            rsi_14=focus.indicators.rsi_14,
            ema_20=focus.indicators.ema_20,
            ema_60=focus.indicators.ema_60,
            ema_120=focus.indicators.ema_120,
            bb_position=focus.indicators.bb_position,
            volume_z_score=focus.indicators.volume_z_score,
            momentum_score=focus.indicators.momentum_score,
            trend_state=focus.indicators.trend_state,
        ),
        recent_bars=[
            SymbolRecentBar(
                bar_time=bar.bar_time,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in focus.bars
        ],
        position=position,
        alerts=list(alerts),
        news=list(news),
        regime=_regime_context(),
        watchpoints=list(focus.watchpoints),
        interpretation=focus.interpretation,
        setup_hint=None,
    )


def _resolve_focus(ticker: str | None) -> tuple[str, FocusTicker | None]:
    normalised = (ticker or SYMBOL_LAB_DEFAULT_TICKER).strip().upper()
    if not normalised:
        normalised = SYMBOL_LAB_DEFAULT_TICKER
    return normalised, FOCUS_TICKERS.get(normalised)


def _missing_payload(ticker: str) -> SymbolLabResponse:
    return SymbolLabResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        header=SymbolLabHeader(
            ticker=ticker,
            timeframe="1d",
            latest_close=None,
            latest_time=None,
            data_status="MISSING",
        ),
        technical=IndicatorSnapshot(),
        recent_bars=[],
        position=None,
        alerts=[],
        news=[],
        regime=_regime_context(),
        watchpoints=[
            f"No stored market bar or indicator snapshot exists for {ticker}.",
        ],
        interpretation=(
            f"{ticker} has no stored market bars or indicator snapshots in "
            "the v0 fixture set."
        ),
        setup_hint=(
            f"{ticker} is not in the Slice 13.7 fixture set. "
            f"Supported tickers: {', '.join(sorted(FOCUS_TICKERS.keys()))}."
        ),
    )


__all__ = ["SYMBOL_LAB_DEFAULT_TICKER", "symbol_lab_fixture"]
