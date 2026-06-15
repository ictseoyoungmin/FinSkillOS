"""GET /api/market-kernel — Slice 13.7 / 24.

Fixture fallback wrapper around the Market Kernel read model. Slice 24
promotes the endpoint to DB-backed mode when stored market bars are
available. The route never calls an external provider during page
rendering; provider refresh is handled by System Ops / scripts.
"""

from __future__ import annotations

from collections import namedtuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from api import coverage as cov
from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import market_kernel_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import (
    EventOverlayItem,
    MarketBarPoint,
    MarketKernelDataState,
    MarketKernelResponse,
)
from api.timeutil import iso as _iso
from api.timeutil import to_utc as _as_utc
from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.db.repositories import IndicatorRepository, MarketRepository

router = APIRouter(tags=["market-kernel"])
UTC = timezone.utc

# Timeframes the Market Kernel chart offers (1D / 1W / 1M in the UI). The route
# is DB-read-only: a timeframe with no stored bars yields an explicit MISSING
# state rather than a provider call during render.
SUPPORTED_MARKET_TIMEFRAMES = {"1d", "1wk", "1mo"}
_MARKET_TIMEFRAME_ALIASES = {
    "1w": "1wk",
    "1week": "1wk",
    "1m": "1mo",
    "1mon": "1mo",
    "1month": "1mo",
}


@router.get(
    "/market-kernel",
    response_model=MarketKernelResponse,
    summary="Market Kernel snapshot for a single ticker (fixture-first in v0).",
)
def market_kernel(
    ticker: str | None = Query(
        default=None,
        description=(
            "Uppercased focus ticker (NVDA / TSLA / AAPL / MSFT / SMH). "
            "Defaults to NVDA when omitted. Unknown tickers return a "
            "MISSING-status payload with a setup hint."
        ),
    ),
    timeframe: str = Query(
        default=DEFAULT_TIMEFRAME,
        description="Chart timeframe: 1d, 1wk, or 1mo (1d default).",
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> MarketKernelResponse:
    if use_fixture:
        return market_kernel_fixture(ticker)

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(market_kernel_fixture(ticker))

        resolved_ticker = _normalize_ticker(ticker)
        resolved_timeframe = _normalize_timeframe(timeframe)
        now = datetime.now(tz=UTC)
        market_repo = MarketRepository(session)
        bars = [
            bar
            for bar in market_repo.list_bars(resolved_ticker, resolved_timeframe)
            if _as_utc(bar.bar_time) <= now
        ]
        # Weekly / monthly bars are not stored (the worker refreshes 1d) — resample
        # the daily series so the 1W / 1M timeframe buttons actually change the
        # chart instead of returning an empty MISSING state.
        if not bars and resolved_timeframe in {"1wk", "1mo"}:
            daily = [
                bar
                for bar in market_repo.list_bars(resolved_ticker, "1d")
                if _as_utc(bar.bar_time) <= now
            ]
            bars = _resample_bars(daily, resolved_timeframe)
        indicator_rows = IndicatorRepository(session).list_for(
            resolved_ticker, resolved_timeframe
        )
        usable_indicators = [
            row for row in indicator_rows if _as_utc(row.snapshot_time) <= now
        ]
        # No indicators are stored for resampled timeframes — fall back to the
        # latest daily snapshot so the indicator panel stays populated.
        if not usable_indicators and resolved_timeframe != "1d":
            usable_indicators = [
                row
                for row in IndicatorRepository(session).list_for(resolved_ticker, "1d")
                if _as_utc(row.snapshot_time) <= now
            ]
        # Only trust an indicator snapshot that has a backing (deduped) bar, so
        # the snapshot panel can never lead the chart with a stale row left over
        # from removed source data. Fall back to the latest usable row if none
        # align (edge tickers whose snapshot times differ from bar times).
        bar_times = {_as_utc(bar.bar_time) for bar in bars}
        backed_indicators = [
            row for row in usable_indicators if _as_utc(row.snapshot_time) in bar_times
        ]
        candidates = backed_indicators or usable_indicators
        latest_indicator = candidates[-1] if candidates else None
        return _live_response(
            session=session,
            ticker=resolved_ticker,
            timeframe=resolved_timeframe,
            bars=bars,
            latest_indicator=latest_indicator,
        )


def _live_response(
    *,
    session,
    ticker: str,
    timeframe: str = DEFAULT_TIMEFRAME,
    bars: list,
    latest_indicator,
) -> MarketKernelResponse:
    generated_at = datetime.now(tz=UTC).isoformat()
    payload = market_kernel_fixture(ticker)
    payload.generated_at = generated_at
    payload.source = "live"
    payload.system_status = SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0)
    events = _event_overlay(session, ticker)
    overlay_status = "AVAILABLE" if events else "MISSING"
    payload.data_state = MarketKernelDataState(
        chart_status="MISSING",
        chart_evidence="missing",
        coverage_level="EMPTY",
        evidence_coverage_percent=0,
        bar_count=0,
        latest_bar_at=None,
        indicator_status="MISSING",
        event_overlay_status=overlay_status,
        missing_summary=f"{ticker} needs stored bars and indicators.",
        source_note=(
            "Live DB is reachable, but no stored market bars exist for "
            "this ticker."
        ),
        refresh_note=(
            "Run System Ops market-bar refresh before expecting chart "
            "context."
        ),
    )

    if not bars:
        payload.judgment = judgment(
            "TECHNICAL SIGNAL JUDGMENT",
            "Data Missing",
            "for Stored Symbol",
            f"{ticker} has no stored market bars in the local DB.",
            28,
        )
        payload.drivers = drivers(
            ("0", "Stored bars", "No DB-backed bar series is available."),
            ("MISSING", "Data status", "The page is showing unavailable-state context."),
            ("Live DB", "Source", "The database is reachable, but this ticker has no bars."),
        )
        payload.conflicts = conflicts(
            (
                "Live DB vs missing ticker",
                "The adapter is reachable but cannot support a technical read without bars.",
            ),
        )
        payload.integrated_interpretation = interpretation(
            "No technical judgment is available for the selected ticker.",
            "The route avoids filling DB gaps with fixture bars once live mode is active.",
            "Run the System Ops market-bar refresh protocol or select a stored symbol.",
        )
        payload.review_watchpoints = watchpoints(
            ("Stored bars", "Refresh market bars before using this ticker context."),
        )
        payload.header.ticker = ticker
        payload.header.label = ticker
        payload.header.timeframe = timeframe
        payload.header.latest_close = None
        payload.header.latest_time = None
        payload.header.data_status = "MISSING"
        payload.bars = []
        payload.indicators.rsi_14 = None
        payload.indicators.ema_20 = None
        payload.indicators.ema_60 = None
        payload.indicators.ema_120 = None
        payload.indicators.bb_position = None
        payload.indicators.volume_z_score = None
        payload.indicators.momentum_score = None
        payload.indicators.trend_state = None
        payload.events = events
        payload.watchpoints = [
            f"No stored market bars exist for {ticker}.",
            "Use System Ops market-bar refresh before expecting live chart context.",
        ]
        payload.interpretation = (
            f"{ticker} has no stored bar series in the local database. "
            "The Market Kernel is live-aware but will not invent chart evidence."
        )
        payload.setup_hint = (
            f"Run System Ops → Refresh market bars with {ticker} in "
            "FINSKILLOS_MARKET_REFRESH_TICKERS."
        )
        return payload

    visible_bars = bars[-120:]
    latest_bar = visible_bars[-1]
    indicator_status = _data_state_indicator_status(latest_indicator)
    coverage_level = cov.coverage_level(
        bar_count=len(bars),
        indicator_status=indicator_status,
    )
    payload.judgment = judgment(
        "TECHNICAL SIGNAL JUDGMENT",
        _trend_title(latest_indicator),
        "from Stored Bars",
        f"{ticker} has {len(bars)} stored {DEFAULT_TIMEFRAME} bars in the local DB.",
        74 if latest_indicator is not None else 58,
    )
    payload.drivers = drivers(
        (str(len(bars)), "Stored bars", "DB-backed OHLCV rows are available."),
        (
            _indicator_status(latest_indicator),
            "Indicator snapshot",
            "Latest stored indicator row attached when available.",
        ),
        ("Live DB", "Source", "Read from local storage; no provider call during render."),
    )
    payload.conflicts = conflicts(
        (
            "Stored bars vs live feed",
            "The chart reflects the latest local refresh, not a streaming provider.",
        ),
        (
            "Bars vs indicators",
            "Indicator fields can be partial when calculation has not run after refresh.",
        ),
    )
    payload.integrated_interpretation = interpretation(
        "Market Kernel is reading stored technical evidence from the local DB.",
        "Stored bars make the chart inspectable without introducing page-load provider risk.",
        "Freshness depends on the latest System Ops refresh and indicator calculation.",
    )
    payload.review_watchpoints = watchpoints(
        ("Refresh timestamp", "Check /api/system-status for latest market bar time."),
        ("Indicator coverage", "Run indicator calculation if fields remain partial."),
    )
    payload.header.ticker = ticker
    payload.header.label = ticker
    payload.header.timeframe = timeframe
    payload.header.latest_close = latest_bar.close
    payload.header.latest_time = _iso(latest_bar.bar_time)
    payload.header.data_status = "OK" if latest_indicator is not None else "PARTIAL"
    payload.data_state = MarketKernelDataState(
        chart_status=payload.header.data_status,
        chart_evidence="stored",
        coverage_level=coverage_level,
        evidence_coverage_percent=cov.evidence_coverage_percent(
            bar_count=len(bars),
            indicator_status=indicator_status,
        ),
        bar_count=len(bars),
        latest_bar_at=_iso(latest_bar.bar_time),
        indicator_status=indicator_status,
        event_overlay_status=overlay_status,
        missing_summary=cov.missing_summary(
            domain="market-kernel",
            ticker=ticker,
            bar_count=len(bars),
            coverage_level=coverage_level,
            indicator_status=indicator_status,
        ),
        source_note="Read from local DB; no provider call during page render.",
        refresh_note=(
            "Freshness depends on the latest System Ops refresh and "
            "indicator calculation."
        ),
    )
    payload.bars = [
        MarketBarPoint(
            bar_time=_iso(bar.bar_time),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in visible_bars
    ]
    payload.indicators.rsi_14 = getattr(latest_indicator, "rsi_14", None)
    payload.indicators.ema_20 = getattr(latest_indicator, "ema_20", None)
    payload.indicators.ema_60 = getattr(latest_indicator, "ema_60", None)
    payload.indicators.ema_120 = getattr(latest_indicator, "ema_120", None)
    payload.indicators.bb_position = _bb_position(latest_bar.close, latest_indicator)
    payload.indicators.volume_z_score = getattr(latest_indicator, "volume_zscore", None)
    payload.indicators.momentum_score = getattr(latest_indicator, "momentum_score", None)
    payload.indicators.trend_state = getattr(latest_indicator, "trend_state", None)
    payload.events = events
    payload.watchpoints = [
        "Stored bars are local snapshots, not a streaming quote feed.",
        "Recompute indicators after refreshing market bars for full context.",
    ]
    payload.interpretation = (
        f"{ticker} technical context is based on {len(bars)} stored bars. "
        "Use this as evidence context, not an entry or exit instruction."
    )
    payload.setup_hint = None
    return payload


_ResampledBar = namedtuple("_ResampledBar", "bar_time open high low close volume")


def _resample_bars(daily: list, timeframe: str) -> list:
    """Aggregate stored daily bars into weekly / monthly OHLCV candles.

    Week buckets start Monday; month buckets on the 1st. Open = first day's open,
    Close = last day's close, High/Low = extremes, Volume = sum. Deterministic and
    offline — no provider call."""

    ordered = sorted(daily, key=lambda bar: _as_utc(bar.bar_time))
    buckets: dict = {}
    order: list = []
    for bar in ordered:
        day = _as_utc(bar.bar_time).date()
        if timeframe == "1wk":
            key = day - timedelta(days=day.weekday())
        else:  # 1mo
            key = day.replace(day=1)
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(bar)

    out: list = []
    for key in order:
        group = buckets[key]
        highs = [b.high for b in group if b.high is not None]
        lows = [b.low for b in group if b.low is not None]
        volumes = [b.volume for b in group if b.volume is not None]
        out.append(
            _ResampledBar(
                bar_time=group[-1].bar_time,  # most recent day in the bucket
                open=group[0].open,
                high=max(highs) if highs else group[-1].close,
                low=min(lows) if lows else group[-1].close,
                close=group[-1].close,
                volume=sum(volumes, Decimal("0")) if volumes else None,
            )
        )
    return out


def _normalize_ticker(ticker: str | None) -> str:
    normalized = (ticker or "NVDA").strip().upper()
    return normalized or "NVDA"


def _normalize_timeframe(timeframe: str | None) -> str:
    normalized = (timeframe or DEFAULT_TIMEFRAME).strip().lower()
    normalized = _MARKET_TIMEFRAME_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_MARKET_TIMEFRAMES:
        return DEFAULT_TIMEFRAME
    return normalized


def _event_overlay(session, ticker: str, *, limit: int = 6) -> list[EventOverlayItem]:
    """Upcoming Catalyst Watch events relevant to ``ticker`` for the chart overlay.

    An event is relevant when the ticker is among its linked tickers, or when it
    is a market-wide macro event (no ticker link — e.g. FOMC / CPI). Scored via
    the Slice-11 EventRiskService for the tone; descriptive only.
    """
    from finskillos.services.event_risk_service import EventRiskService
    from finskillos.services.event_service import EventService

    today = datetime.now(tz=UTC).date()
    upcoming = EventService(session).list_upcoming(today=today, limit=30)
    if not upcoming:
        return []

    risk_service = EventRiskService(session)
    normalized = ticker.upper()
    items: list[EventOverlayItem] = []
    for event in upcoming:
        breakdown = risk_service.score(event, today=today)
        affected = {tick.upper() for tick in breakdown.affected_tickers}
        is_market_wide = not affected
        if normalized not in affected and not is_market_wide:
            continue
        scope = "Market-wide" if is_market_wide else f"{breakdown.risk_label.title()} relevance"
        items.append(
            EventOverlayItem(
                days_to_event=breakdown.days_to_event,
                title=event.title,
                subtitle=f"{event.event_type.replace('_', ' ').title()} · {scope}",
                tag=event.date_status.title(),
                tone=_overlay_tone(breakdown.risk_label),
            )
        )
        if len(items) >= limit:
            break
    return items


def _overlay_tone(risk_label: str) -> str:
    return {
        "CRITICAL": "danger",
        "HIGH": "warning",
        "MODERATE": "info",
        "LOW": "neutral",
    }.get(risk_label, "neutral")


def _indicator_status(latest_indicator) -> str:
    if latest_indicator is None:
        return "PARTIAL"
    return latest_indicator.trend_state or "AVAILABLE"


def _data_state_indicator_status(latest_indicator) -> str:
    if latest_indicator is None:
        return "MISSING"
    fields = (
        "rsi_14",
        "ema_20",
        "ema_60",
        "ema_120",
        "volume_zscore",
        "momentum_score",
        "trend_state",
    )
    values = [getattr(latest_indicator, field, None) for field in fields]
    if all(value is not None for value in values):
        return "AVAILABLE"
    return "PARTIAL"


def _trend_title(latest_indicator) -> str:
    if latest_indicator is None or not latest_indicator.trend_state:
        return "Stored Tape"
    return latest_indicator.trend_state.title()


def _bb_position(close: Decimal, latest_indicator) -> Decimal | None:
    if latest_indicator is None:
        return None
    upper = getattr(latest_indicator, "bb_upper", None)
    lower = getattr(latest_indicator, "bb_lower", None)
    if upper is None or lower is None or upper == lower:
        return None
    return (close - lower) / (upper - lower)


__all__ = ["router"]
