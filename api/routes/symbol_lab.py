"""GET /api/symbol-lab — Slice 13.7 / 27.

Fixture fallback wrapper around the Symbol Lab read model. Slice 27
promotes the endpoint to DB-backed mode when stored market bars are
available. The route never calls an external provider during page
rendering; provider refresh is handled by System Ops / scripts / worker.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import symbol_lab_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.schemas.common import SystemStatus
from api.schemas.market_kernel import IndicatorSnapshot
from api.schemas.symbol_lab import (
    SymbolAlert,
    SymbolLabHeader,
    SymbolLabResponse,
    SymbolPosition,
    SymbolRecentBar,
)
from finskillos.data_sources import DEFAULT_TIMEFRAME, DEFAULT_US_TICKER_UNIVERSE
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    IndicatorRepository,
    MarketRepository,
    PositionRepository,
)

router = APIRouter(tags=["symbol-lab"])
UTC = timezone.utc
SINGLE_POSITION_REVIEW_THRESHOLD = Decimal("10000000")


@router.get(
    "/symbol-lab",
    response_model=SymbolLabResponse,
    summary="Symbol Lab snapshot for a single ticker (fixture-first in v0).",
)
def symbol_lab(
    ticker: str | None = Query(
        default=None,
        description=(
            "Uppercased ticker (NVDA / TSLA / AAPL / MSFT / SMH). Defaults "
            "to TSLA when omitted. Unknown tickers return a MISSING-status "
            "payload with a setup hint."
        ),
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> SymbolLabResponse:
    if use_fixture:
        return symbol_lab_fixture(ticker)

    with get_session_scope() as session:
        if session is None:
            return symbol_lab_fixture(ticker)

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
        accounts = AccountRepository(session).list_all()
        account = accounts[0] if accounts else None
        positions = PositionRepository(session).list_for_account(account.id) if account else []
        position = (
            PositionRepository(session).get_by_account_and_ticker(
                account.id, resolved_ticker
            )
            if account
            else None
        )
        alerts = AlertRepository(session).list_active(account.id) if account else []
        return _live_response(
            ticker=resolved_ticker,
            bars=bars,
            latest_indicator=latest_indicator,
            position=position,
            positions=positions,
            alerts=alerts,
        )


def _live_response(
    *,
    ticker: str,
    bars: list,
    latest_indicator,
    position,
    positions: list,
    alerts: list,
) -> SymbolLabResponse:
    generated_at = datetime.now(tz=UTC).isoformat()
    payload = symbol_lab_fixture(ticker)
    symbol_alerts = _symbol_alerts(ticker, alerts)
    payload.generated_at = generated_at
    payload.source = "live"
    payload.system_status = SystemStatus(
        db="LIVE",
        mode="READ_MODE",
        guard_count=len(symbol_alerts),
    )
    payload.symbol_universe = _symbol_universe(ticker)
    payload.position = _position_context(position, positions)
    payload.alerts = symbol_alerts
    payload.news = []

    if not bars:
        payload.judgment = judgment(
            f"SYMBOL JUDGMENT · {ticker}",
            "Data Missing",
            "for Stored Symbol",
            f"{ticker} has no stored market bars in the local DB.",
            28,
        )
        payload.drivers = drivers(
            ("0", "Stored bars", "No DB-backed bar series is available."),
            (
                "MISSING",
                "Data status",
                "The page is showing unavailable-state symbol context.",
            ),
            (
                str(len(symbol_alerts)),
                "Active alerts",
                "Position guard context is attached when stored locally.",
            ),
        )
        payload.conflicts = conflicts(
            (
                "Live DB vs missing symbol",
                "The database is reachable, but this ticker has no stored bars.",
            ),
        )
        payload.integrated_interpretation = interpretation(
            "No symbol judgment is available for the selected ticker.",
            "The route avoids filling DB gaps with fixture bars once live mode is active.",
            "Run the System Ops market-bar refresh protocol or select a stored symbol.",
        )
        payload.review_watchpoints = watchpoints(
            ("Stored bars", "Refresh market bars before using this ticker context."),
            ("Symbol image", "Logo/avatar retrieval is deferred to a provider cache slice."),
        )
        payload.header = SymbolLabHeader(
            ticker=ticker,
            timeframe=DEFAULT_TIMEFRAME,
            latest_close=None,
            latest_time=None,
            data_status="MISSING",
        )
        payload.technical = IndicatorSnapshot()
        payload.recent_bars = []
        payload.watchpoints = [
            f"No stored market bars exist for {ticker}.",
            "Use System Ops market refresh before expecting live symbol context.",
            "Symbol images are not fetched during page render.",
        ]
        payload.interpretation = (
            f"{ticker} has no stored bar series in the local database. "
            "Symbol Lab is live-aware but will not invent chart evidence."
        )
        payload.setup_hint = (
            f"Run System Ops -> Refresh market bars with {ticker} in "
            "FINSKILLOS_MARKET_REFRESH_TICKERS."
        )
        return payload

    visible_bars = bars[-120:]
    latest_bar = visible_bars[-1]
    payload.judgment = judgment(
        f"SYMBOL JUDGMENT · {ticker}",
        _trend_title(latest_indicator),
        "from Stored Symbol Evidence",
        f"{ticker} has {len(bars)} stored {DEFAULT_TIMEFRAME} bars in the local DB.",
        76 if latest_indicator is not None else 58,
    )
    payload.drivers = drivers(
        (str(len(bars)), "Stored bars", "DB-backed OHLCV rows are available."),
        (
            _indicator_status(latest_indicator),
            "Indicator snapshot",
            "Latest stored indicator row attached when available.",
        ),
        (
            "HELD" if position is not None else "WATCH_ONLY",
            "Position context",
            "Live holdings are attached when the symbol exists in positions.",
        ),
    )
    payload.conflicts = conflicts(
        (
            "Stored bars vs live feed",
            "The chart reflects the latest local refresh, not a streaming quote feed.",
        ),
        (
            "Symbol context vs portfolio context",
            "A symbol can look technically constructive while position constraints remain active.",
        ),
    )
    payload.integrated_interpretation = interpretation(
        "Symbol Lab is reading stored symbol evidence from the local DB.",
        "Stored bars and indicators make the ticker inspectable without page-load provider risk.",
        "Freshness depends on the latest System Ops refresh and indicator calculation.",
    )
    payload.review_watchpoints = watchpoints(
        ("Refresh timestamp", "Check /api/system-status for latest market bar time."),
        ("Position context", "Review active alerts if this symbol is currently held."),
        ("Symbol image", "Logo/avatar retrieval is deferred to a provider cache slice."),
    )
    payload.header = SymbolLabHeader(
        ticker=ticker,
        timeframe=DEFAULT_TIMEFRAME,
        latest_close=latest_bar.close,
        latest_time=_iso(latest_bar.bar_time),
        data_status="OK" if latest_indicator is not None else "PARTIAL",
    )
    payload.technical = IndicatorSnapshot(
        rsi_14=getattr(latest_indicator, "rsi_14", None),
        ema_20=getattr(latest_indicator, "ema_20", None),
        ema_60=getattr(latest_indicator, "ema_60", None),
        ema_120=getattr(latest_indicator, "ema_120", None),
        bb_position=_bb_position(latest_bar.close, latest_indicator),
        volume_z_score=getattr(latest_indicator, "volume_zscore", None),
        momentum_score=getattr(latest_indicator, "momentum_score", None),
        trend_state=getattr(latest_indicator, "trend_state", None),
    )
    payload.recent_bars = [
        SymbolRecentBar(
            bar_time=_iso(bar.bar_time),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in visible_bars
    ]
    payload.watchpoints = [
        "Stored bars are local snapshots, not a streaming quote feed.",
        "Recompute indicators after refreshing market bars for full context.",
        "Symbol images are not fetched during page render.",
    ]
    if position is not None and position.market_value > SINGLE_POSITION_REVIEW_THRESHOLD:
        payload.watchpoints.append(
            "Position value is above the configured single-position review threshold."
        )
    payload.interpretation = (
        f"{ticker} symbol context is based on {len(bars)} stored bars. "
        "Use this as evidence context, not an entry or exit instruction."
    )
    payload.setup_hint = None
    return payload


def _position_context(position, positions: list) -> SymbolPosition | None:
    if position is None:
        return None
    total_value = sum((item.market_value for item in positions), Decimal("0"))
    portfolio_weight = (
        position.market_value / total_value if total_value and total_value > 0 else None
    )
    return SymbolPosition(
        ticker=position.ticker,
        sector=position.sector,
        theme=position.theme,
        strategy_type=position.strategy_type,
        market_value=position.market_value,
        portfolio_weight=portfolio_weight,
        pnl_pct=position.pnl_pct,
        quantity=position.quantity,
        thesis=position.thesis,
        over_single_position_limit=(
            position.market_value > SINGLE_POSITION_REVIEW_THRESHOLD
        ),
    )


def _symbol_alerts(ticker: str, alerts: list) -> list[SymbolAlert]:
    normalized = ticker.upper()
    result: list[SymbolAlert] = []
    for alert in alerts:
        payload = alert.payload or {}
        payload_tickers = {
            str(value).upper()
            for key in ("ticker", "symbol", "position", "positions")
            for value in _payload_values(payload.get(key))
        }
        text = " ".join(
            part or "" for part in (alert.guard_name, alert.title, alert.message)
        ).upper()
        if normalized not in payload_tickers and normalized not in text:
            continue
        result.append(
            SymbolAlert(
                guard_name=alert.guard_name,
                severity=alert.severity,
                title=alert.title,
                message=alert.message or "",
                alert_date=alert.alert_date,
            )
        )
    return result


def _payload_values(value) -> list:
    if value is None:
        return []
    if isinstance(value, list | tuple | set):
        return list(value)
    return [value]


def _symbol_universe(selected_ticker: str):
    rows = []
    seen: set[str] = set()
    for symbol in DEFAULT_US_TICKER_UNIVERSE:
        rows.append(_universe_row(symbol))
        seen.add(symbol)
    if selected_ticker not in seen:
        rows.insert(0, _universe_row(selected_ticker))
    return rows


def _universe_row(symbol: str):
    from api.schemas.market_kernel import UniverseTicker

    kind = "FOCUS"
    if symbol in {"SPY", "QQQ"}:
        kind = "INDEX_ETF"
    elif symbol in {"SMH", "SOXX"}:
        kind = "SECTOR_ETF"
    elif symbol in {"VIX", "US10Y", "DXY"}:
        kind = "MACRO_PROXY"
    return UniverseTicker(symbol=symbol, label=_symbol_label(symbol), kind=kind)


def _symbol_label(symbol: str) -> str:
    labels = {
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
    return labels.get(symbol, symbol)


def _normalize_ticker(ticker: str | None) -> str:
    normalized = (ticker or "TSLA").strip().upper()
    return normalized or "TSLA"


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
