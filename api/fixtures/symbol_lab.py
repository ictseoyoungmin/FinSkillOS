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
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.fixtures.analysis_workspace import _regime_context
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import IndicatorSnapshot
from api.schemas.symbol_lab import (
    SymbolAlert,
    SymbolIdentity,
    SymbolLabDataState,
    SymbolLabHeader,
    SymbolLabResponse,
    SymbolNewsItem,
    SymbolPosition,
    SymbolRecentBar,
    SymbolSubscriptionState,
    UniverseTicker,
)

SYMBOL_LAB_DEFAULT_TICKER = "TSLA"

_SYMBOL_UNIVERSE: tuple[UniverseTicker, ...] = (
    UniverseTicker(symbol="NVDA", label="NVIDIA", kind="FOCUS"),
    UniverseTicker(symbol="TSLA", label="Tesla", kind="FOCUS"),
    UniverseTicker(symbol="AAPL", label="Apple", kind="FOCUS"),
    UniverseTicker(symbol="MSFT", label="Microsoft", kind="FOCUS"),
    UniverseTicker(symbol="SMH", label="Semiconductor ETF", kind="SECTOR_ETF"),
)

_SYMBOL_NAMES: dict[str, str] = {
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "SMH": "Semiconductor ETF",
    "SOXX": "Semiconductor ETF",
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "VIX": "Volatility Proxy",
    "US10Y": "10Y Yield Proxy",
    "DXY": "USD Index Proxy",
}

_SYMBOL_COLORS: dict[str, str] = {
    "NVDA": "#15803d",
    "TSLA": "#b91c1c",
    "AAPL": "#334155",
    "MSFT": "#2563eb",
    "AMZN": "#b45309",
    "SMH": "#7c3aed",
    "SOXX": "#4338ca",
    "SPY": "#0f766e",
    "QQQ": "#1d4ed8",
    "VIX": "#dc2626",
    "US10Y": "#a16207",
    "DXY": "#475569",
}


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


def symbol_lab_fixture(
    ticker: str | None = None,
    *,
    timeframe: str = "1d",
) -> SymbolLabResponse:
    """Build the Symbol Lab response for ``ticker`` (uppercased)."""

    resolved, focus = _resolve_focus(ticker)

    if focus is None:
        return _missing_payload(resolved, timeframe=timeframe)

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
        judgment=judgment(
            f"SYMBOL JUDGMENT · {focus.symbol}",
            "Recovering but",
            "Constrained",
            (
                f"{focus.symbol} combines stored technical evidence, "
                "position context, alerts, and news into a descriptive view."
            ),
            66,
        ),
        drivers=drivers(
            (
                focus.indicators.trend_state or "UNKNOWN",
                "Trend state",
                "Latest stored indicator state.",
            ),
            (
                str(len(alerts)),
                "Active alerts",
                "Position and risk context attached to the symbol.",
            ),
            (str(len(news)), "News items", "Recent symbol-linked headlines in the fixture."),
        ),
        conflicts=conflicts(
            (
                "Technical recovery vs risk context",
                "Signal evidence must be read beside position and alert state.",
            ),
            (
                "Ticker-specific vs portfolio-level",
                "Symbol context may differ from the broader operating posture.",
            ),
        ),
        integrated_interpretation=interpretation(
            f"{focus.symbol} is recovering but remains constrained by review conditions.",
            "The page binds technical, position, alert, and news evidence "
            "before forming a symbol read.",
            "Fresh bars, alerts, or news can change the confidence score.",
        ),
        review_watchpoints=watchpoints(
            ("Position guard", "Recheck any active single-position or concentration alert."),
            ("News tone", "Watch whether symbol-linked news clusters in one theme."),
        ),
        symbol_universe=list(_SYMBOL_UNIVERSE),
        identity=symbol_identity(focus.symbol),
        subscription=SymbolSubscriptionState(
            is_subscribed=focus.symbol in {"NVDA", "TSLA", "AAPL", "MSFT", "SMH"},
            update_universe_member=True,
        ),
        data_state=SymbolLabDataState(
            chart_status="OK",
            chart_evidence="stored",
            bar_count=len(focus.bars),
            indicator_status="AVAILABLE",
            logo_source="local_fallback",
            subscription_status=(
                "subscribed"
                if focus.symbol in {"NVDA", "TSLA", "AAPL", "MSFT", "SMH"}
                else "watch_only"
            ),
        ),
        header=SymbolLabHeader(
            ticker=focus.symbol,
            timeframe=timeframe,
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
        safety_caption=(
            "Symbol interpretation (not trade signal). Stored data only · not prediction."
        ),
    )


def _resolve_focus(ticker: str | None) -> tuple[str, FocusTicker | None]:
    normalised = (ticker or SYMBOL_LAB_DEFAULT_TICKER).strip().upper()
    if not normalised:
        normalised = SYMBOL_LAB_DEFAULT_TICKER
    return normalised, FOCUS_TICKERS.get(normalised)


def _missing_payload(ticker: str, *, timeframe: str = "1d") -> SymbolLabResponse:
    return SymbolLabResponse(
        generated_at=FIXTURE_TIMESTAMP,
        source="fixture",
        system_status=SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0),
        judgment=judgment(
            f"SYMBOL JUDGMENT · {ticker}",
            "Data Missing",
            "for Selected Symbol",
            f"{ticker} has no stored symbol evidence yet.",
            30,
        ),
        drivers=drivers(
            ("0", "Stored bars", "No local technical series is available."),
            ("0", "Active alerts", "No symbol-specific guard context is attached."),
            ("0", "News items", "No symbol-linked fixture headlines are available."),
        ),
        conflicts=conflicts(
            (
                "Selected symbol vs stored evidence",
                "The requested ticker can be searched, but no local snapshot is stored yet.",
            ),
        ),
        integrated_interpretation=interpretation(
            "No symbol judgment is available for the selected ticker.",
            "The UI should surface missing evidence instead of inventing symbol context.",
            "A future stored snapshot is required before technical context can be shown.",
        ),
        review_watchpoints=watchpoints(
            ("Stored evidence", "Search any ticker; populated context appears when data exists."),
        ),
        symbol_universe=list(_SYMBOL_UNIVERSE),
        identity=symbol_identity(ticker),
        subscription=SymbolSubscriptionState(is_subscribed=False),
        data_state=SymbolLabDataState(
            chart_status="MISSING",
            chart_evidence="missing",
            bar_count=0,
            indicator_status="MISSING",
            logo_source="local_fallback",
            subscription_status="watch_only",
        ),
        header=SymbolLabHeader(
            ticker=ticker,
            timeframe=timeframe,
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
            f"{ticker} has no stored market bars or indicator snapshots yet."
        ),
        setup_hint=(
            f"{ticker} was searched successfully, but no stored technical snapshot "
            "exists yet."
        ),
        safety_caption=(
            "Symbol interpretation (not trade signal). Stored data only · not prediction."
        ),
    )


def symbol_identity(ticker: str) -> SymbolIdentity:
    normalized = ticker.strip().upper()
    return SymbolIdentity(
        ticker=normalized,
        name=_SYMBOL_NAMES.get(normalized, normalized),
        logo_url=None,
        logo_source="local_fallback",
        avatar_text=_avatar_text(normalized),
        brand_color=_SYMBOL_COLORS.get(normalized, "#475569"),
    )


def _avatar_text(ticker: str) -> str:
    if ticker in {"SPY", "QQQ", "DIA", "IWM", "SMH", "SOXX", "XLK"}:
        return ticker
    letters = "".join(ch for ch in ticker if ch.isalpha())
    return (letters[:2] or ticker[:2] or "?").upper()


__all__ = ["SYMBOL_LAB_DEFAULT_TICKER", "symbol_identity", "symbol_lab_fixture"]
