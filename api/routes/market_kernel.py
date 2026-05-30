"""GET /api/market-kernel — Slice 13.7 / 24.

Fixture fallback wrapper around the Market Kernel read model. Slice 24
promotes the endpoint to DB-backed mode when stored market bars are
available. The route never calls an external provider during page
rendering; provider refresh is handled by System Ops / scripts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import market_kernel_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import (
    MarketBarPoint,
    MarketKernelDataState,
    MarketKernelResponse,
)
from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.db.repositories import IndicatorRepository, MarketRepository

router = APIRouter(tags=["market-kernel"])
UTC = timezone.utc


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
    use_fixture: bool = Depends(use_fixture_flag),
) -> MarketKernelResponse:
    if use_fixture:
        return market_kernel_fixture(ticker)

    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(market_kernel_fixture(ticker))

        resolved_ticker = _normalize_ticker(ticker)
        now = datetime.now(tz=UTC)
        bars = [
            bar
            for bar in MarketRepository(session).list_bars(
                resolved_ticker, DEFAULT_TIMEFRAME
            )
            if _as_utc(bar.bar_time) <= now
        ]
        indicator_rows = IndicatorRepository(session).list_for(
            resolved_ticker, DEFAULT_TIMEFRAME
        )
        usable_indicators = [
            row for row in indicator_rows if _as_utc(row.snapshot_time) <= now
        ]
        latest_indicator = usable_indicators[-1] if usable_indicators else None
        return _live_response(
            ticker=resolved_ticker,
            bars=bars,
            latest_indicator=latest_indicator,
        )


def _live_response(
    *,
    ticker: str,
    bars: list,
    latest_indicator,
) -> MarketKernelResponse:
    generated_at = datetime.now(tz=UTC).isoformat()
    payload = market_kernel_fixture(ticker)
    payload.generated_at = generated_at
    payload.source = "live"
    payload.system_status = SystemStatus(db="LIVE", mode="READ_MODE", guard_count=0)
    payload.data_state = MarketKernelDataState(
        chart_status="MISSING",
        chart_evidence="missing",
        coverage_level="EMPTY",
        evidence_coverage_percent=0,
        bar_count=0,
        latest_bar_at=None,
        indicator_status="MISSING",
        event_overlay_status="MISSING",
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
        payload.header.timeframe = DEFAULT_TIMEFRAME
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
        payload.events = []
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
    coverage_level = _coverage_level(
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
    payload.header.timeframe = DEFAULT_TIMEFRAME
    payload.header.latest_close = latest_bar.close
    payload.header.latest_time = _iso(latest_bar.bar_time)
    payload.header.data_status = "OK" if latest_indicator is not None else "PARTIAL"
    payload.data_state = MarketKernelDataState(
        chart_status=payload.header.data_status,
        chart_evidence="stored",
        coverage_level=coverage_level,
        evidence_coverage_percent=_evidence_coverage_percent(
            bar_count=len(bars),
            indicator_status=indicator_status,
        ),
        bar_count=len(bars),
        latest_bar_at=_iso(latest_bar.bar_time),
        indicator_status=indicator_status,
        event_overlay_status="MISSING",
        missing_summary=_missing_summary(
            ticker=ticker,
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
    payload.events = []
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


def _normalize_ticker(ticker: str | None) -> str:
    normalized = (ticker or "NVDA").strip().upper()
    return normalized or "NVDA"


def _iso(value) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC).isoformat()
        return value.isoformat()
    return str(value)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


def _coverage_level(*, bar_count: int, indicator_status: str) -> str:
    if bar_count <= 0:
        return "EMPTY"
    if bar_count < 20:
        return "SPARSE"
    if indicator_status != "AVAILABLE":
        return "PARTIAL"
    return "COMPLETE"


def _evidence_coverage_percent(*, bar_count: int, indicator_status: str) -> int:
    if bar_count <= 0:
        return 0
    bar_score = min(bar_count / 20, 1.0) * 70
    indicator_score = {
        "AVAILABLE": 30,
        "PARTIAL": 15,
        "MISSING": 0,
    }.get(indicator_status, 0)
    return round(bar_score + indicator_score)


def _missing_summary(
    *,
    ticker: str,
    coverage_level: str,
    indicator_status: str,
) -> str:
    if coverage_level == "COMPLETE":
        return "No missing market-kernel evidence."
    if coverage_level == "EMPTY":
        return f"{ticker} needs stored bars and indicators."
    if coverage_level == "SPARSE":
        return f"{ticker} has fewer than 20 stored bars."
    if indicator_status != "AVAILABLE":
        return f"{ticker} needs a complete indicator snapshot."
    return f"{ticker} evidence is partial."


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
