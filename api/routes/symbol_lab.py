"""GET /api/symbol-lab — Slice 13.7 / 27 / 29.

Fixture fallback wrapper around the Symbol Lab read model. Slice 27
promotes the endpoint to DB-backed mode when stored market bars are
available. Slice 29 also allows an explicit provider preview for
arbitrary searched symbols when the local DB has no stored bars.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from api import coverage as cov
from api.dependencies import get_session_scope, mark_db_unavailable, use_fixture_flag
from api.fixtures import symbol_lab_fixture
from api.fixtures._v42 import conflicts, drivers, interpretation, judgment, watchpoints
from api.fixtures.symbol_lab import symbol_identity
from api.schemas.analysis_workspace import RegimeContext
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
    SymbolSubscriptionFolder,
    SymbolSubscriptionFolderInput,
    SymbolSubscriptionFolderList,
    SymbolSubscriptionFolderMember,
    SymbolSubscriptionState,
)
from api.timeutil import iso as _iso
from api.timeutil import to_utc as _as_utc
from finskillos.data_sources import (
    DEFAULT_TIMEFRAME,
    DEFAULT_US_TICKER_UNIVERSE,
    IndicatorSnapshotDTO,
    MarketDataFetchError,
    MockMarketDataAdapter,
    YahooChartMarketDataAdapter,
)
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    IndicatorRepository,
    MarketRepository,
    PositionRepository,
    SymbolSubscriptionFolderRepository,
    SymbolSubscriptionRepository,
)
from finskillos.services.market_data_service import MarketDataService
from finskillos.services.signal_service import SignalService
from finskillos.services.symbol_logo_service import resolve_symbol_logo_identity
from finskillos.signals import technical

router = APIRouter(tags=["symbol-lab"])
UTC = timezone.utc
SINGLE_POSITION_REVIEW_THRESHOLD = Decimal("10000000")
SUPPORTED_SYMBOL_TIMEFRAMES = {"5m", "15m", "1h", "1d", "1wk", "1mo", "1y"}
TIMEFRAME_ALIASES = {"1w": "1wk", "1mon": "1mo"}


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
    timeframe: str = Query(
        default=DEFAULT_TIMEFRAME,
        description="Chart timeframe: 5m, 15m, 1h, 1d, 1wk, 1mo, or 1y.",
    ),
    use_fixture: bool = Depends(use_fixture_flag),
) -> SymbolLabResponse:
    if use_fixture:
        return symbol_lab_fixture(
            ticker,
            timeframe=_normalize_timeframe(timeframe),
        )
    return _read_symbol_lab(ticker, timeframe=timeframe)


def _read_symbol_lab(
    ticker: str | None,
    *,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> SymbolLabResponse:
    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(
                symbol_lab_fixture(
                    ticker,
                    timeframe=_normalize_timeframe(timeframe),
                )
            )

        resolved_ticker = _normalize_ticker(ticker)
        resolved_timeframe = _normalize_timeframe(timeframe)
        provider_note = _refresh_symbol_chart_data(
            session,
            resolved_ticker,
            resolved_timeframe,
        )
        now = datetime.now(tz=UTC)
        bars = [
            bar
            for bar in MarketRepository(session).list_bars(
                resolved_ticker, resolved_timeframe
            )
            if _as_utc(bar.bar_time) <= now
        ]
        indicator_rows = IndicatorRepository(session).list_for(
            resolved_ticker, resolved_timeframe
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
        subscription = _get_subscription_safe(session, resolved_ticker)
        provider_preview_used = False
        if not bars and _symbol_preview_enabled():
            try:
                preview_bars = YahooChartMarketDataAdapter().fetch_bars(
                    resolved_ticker,
                    timeframe=resolved_timeframe,
                    end=datetime.now(tz=UTC),
                )
                bars = [bar for bar in preview_bars if _as_utc(bar.bar_time) <= now]
                provider_preview_used = bool(bars)
            except MarketDataFetchError as exc:
                provider_note = _provider_note(exc)
                bars = []
        bars = _bars_for_timeframe_window(
            _prefer_provider_bars(bars),
            resolved_timeframe,
        )
        usable_indicators = _indicators_for_bars(usable_indicators, bars)
        if bars and not usable_indicators:
            usable_indicators = _fallback_indicators_from_bars(
                resolved_ticker,
                resolved_timeframe,
                bars,
            )
            latest_indicator = usable_indicators[-1] if usable_indicators else None
        return _live_response(
            session=session,
            ticker=resolved_ticker,
            timeframe=resolved_timeframe,
            bars=bars,
            indicators=usable_indicators,
            latest_indicator=latest_indicator,
            position=position,
            positions=positions,
            alerts=alerts,
            subscription=subscription,
            provider_preview_used=provider_preview_used,
            provider_note=provider_note,
        )


@router.post(
    "/symbol-lab/{ticker}/subscribe",
    response_model=SymbolLabResponse,
    summary="Subscribe a ticker to the local refresh universe.",
)
def subscribe_symbol(
    ticker: str,
    timeframe: str = Query(
        default=DEFAULT_TIMEFRAME,
        description="Response timeframe: 5m, 15m, 1h, 1d, 1wk, 1mo, or 1y.",
    ),
) -> SymbolLabResponse:
    resolved_ticker = _normalize_ticker(ticker)
    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(symbol_lab_fixture(resolved_ticker))

        repo = SymbolSubscriptionRepository(session)
        repo.subscribe(
            resolved_ticker,
            name=symbol_identity(resolved_ticker).name,
        )
        _refresh_subscribed_symbol(session, resolved_ticker)

    return _read_symbol_lab(resolved_ticker, timeframe=timeframe)


@router.post(
    "/symbol-lab/{ticker}/unsubscribe",
    response_model=SymbolLabResponse,
    summary="Deactivate a ticker subscription without deleting historical data.",
)
def unsubscribe_symbol(
    ticker: str,
    timeframe: str = Query(
        default=DEFAULT_TIMEFRAME,
        description="Response timeframe: 5m, 15m, 1h, 1d, 1wk, 1mo, or 1y.",
    ),
) -> SymbolLabResponse:
    resolved_ticker = _normalize_ticker(ticker)
    with get_session_scope() as session:
        if session is None:
            return mark_db_unavailable(symbol_lab_fixture(resolved_ticker))
        SymbolSubscriptionRepository(session).unsubscribe(resolved_ticker)

    return _read_symbol_lab(resolved_ticker, timeframe=timeframe)


@router.get(
    "/symbol-lab/subscription-folders",
    response_model=SymbolSubscriptionFolderList,
    summary="List foldered active symbol subscriptions.",
)
def list_subscription_folders() -> SymbolSubscriptionFolderList:
    with get_session_scope() as session:
        if session is None:
            return SymbolSubscriptionFolderList()
        repo = SymbolSubscriptionFolderRepository(session)
        return SymbolSubscriptionFolderList(
            folders=[_folder_schema(folder) for folder in repo.list_snapshots()]
        )


@router.post(
    "/symbol-lab/subscription-folders",
    response_model=SymbolSubscriptionFolderList,
    summary="Create or update a symbol subscription folder.",
)
def upsert_subscription_folder(
    payload: SymbolSubscriptionFolderInput,
) -> SymbolSubscriptionFolderList:
    error: tuple[int, str] | None = None
    with get_session_scope() as session:
        if session is None:
            return SymbolSubscriptionFolderList()
        repo = SymbolSubscriptionFolderRepository(session)
        try:
            repo.upsert_folder(
                payload.name,
                description=payload.description,
                sort_order=payload.sort_order,
            )
            session.commit()
        except ValueError as exc:
            session.rollback()
            error = (400, str(exc))
        else:
            return SymbolSubscriptionFolderList(
                folders=[_folder_schema(folder) for folder in repo.list_snapshots()]
            )
    if error is not None:
        raise HTTPException(status_code=error[0], detail=error[1])
    return SymbolSubscriptionFolderList()


@router.post(
    "/symbol-lab/subscription-folders/{folder_id}/symbols/{ticker}",
    response_model=SymbolSubscriptionFolderList,
    summary="Assign an active subscribed ticker to a folder.",
)
def add_symbol_to_subscription_folder(
    folder_id: UUID,
    ticker: str,
) -> SymbolSubscriptionFolderList:
    resolved_ticker = _normalize_ticker(ticker)
    error: tuple[int, str] | None = None
    with get_session_scope() as session:
        if session is None:
            return SymbolSubscriptionFolderList()
        repo = SymbolSubscriptionFolderRepository(session)
        try:
            repo.add_symbol(folder_id, resolved_ticker)
            session.commit()
        except ValueError as exc:
            session.rollback()
            status = (
                404
                if str(exc) in {"folder_not_found", "subscription_not_found"}
                else 400
            )
            error = (status, str(exc))
        else:
            return SymbolSubscriptionFolderList(
                folders=[_folder_schema(folder) for folder in repo.list_snapshots()]
            )
    if error is not None:
        raise HTTPException(status_code=error[0], detail=error[1])
    return SymbolSubscriptionFolderList()


@router.delete(
    "/symbol-lab/subscription-folders/{folder_id}/symbols/{ticker}",
    response_model=SymbolSubscriptionFolderList,
    summary="Remove a ticker from a subscription folder.",
)
def remove_symbol_from_subscription_folder(
    folder_id: UUID,
    ticker: str,
) -> SymbolSubscriptionFolderList:
    resolved_ticker = _normalize_ticker(ticker)
    with get_session_scope() as session:
        if session is None:
            return SymbolSubscriptionFolderList()
        repo = SymbolSubscriptionFolderRepository(session)
        repo.remove_symbol(folder_id, resolved_ticker)
        session.commit()
        return SymbolSubscriptionFolderList(
            folders=[_folder_schema(folder) for folder in repo.list_snapshots()]
        )


def _live_response(
    *,
    session,
    ticker: str,
    timeframe: str,
    bars: list,
    indicators: list,
    latest_indicator,
    position,
    positions: list,
    alerts: list,
    subscription,
    provider_preview_used: bool = False,
    provider_note: str | None = None,
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
    payload.identity = _symbol_identity(session, ticker)
    payload.subscription = _subscription_state(subscription)
    payload.data_state = _data_state_for(
        chart_status="MISSING",
        chart_evidence="missing",
        bars=[],
        latest_indicator=None,
        identity=payload.identity,
        subscription=payload.subscription,
        provider_note=provider_note,
    )
    payload.position = _position_context(position, positions)
    payload.alerts = symbol_alerts
    # Live news + regime overlays (the fixture base ships sample rows that would
    # otherwise leak into live mode). Empty/None when the DB has nothing stored →
    # the panels show their honest empty state.
    payload.news = _live_symbol_news(session, ticker)
    payload.regime = _live_regime_context(session, bars)

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
        missing_watchpoints = [
            ("Stored bars", "Refresh market bars before using this ticker context."),
            (
                "Symbol logo",
                "Logo metadata uses the configured provider cache when available.",
            ),
        ]
        if provider_note:
            missing_watchpoints.append(
                (
                    "Provider preview",
                    f"yfinance preview did not return usable bars: {provider_note}",
                )
            )
        payload.review_watchpoints = watchpoints(*missing_watchpoints)
        payload.header = SymbolLabHeader(
            ticker=ticker,
            timeframe=timeframe,
            latest_close=None,
            latest_time=None,
            data_status="MISSING",
        )
        payload.technical = IndicatorSnapshot()
        payload.recent_bars = []
        payload.data_state = _data_state_for(
            chart_status="MISSING",
            chart_evidence="missing",
            bars=[],
            latest_indicator=None,
            identity=payload.identity,
            subscription=payload.subscription,
            provider_note=provider_note,
        )
        payload.watchpoints = [
            f"No stored market bars exist for {ticker}.",
            "Use System Ops market refresh before expecting live symbol context.",
            "Ticker logos use cached provider metadata when configured.",
        ]
        if provider_note:
            payload.watchpoints.append(
                f"Provider preview did not return usable bars: {provider_note}"
            )
        payload.interpretation = (
            f"{ticker} has no stored bar series in the local database. "
            "Symbol Lab is live-aware but will not invent chart evidence."
        )
        payload.setup_hint = _missing_symbol_setup_hint(ticker, provider_note)
        return payload

    visible_bars = bars[-120:]
    latest_bar = visible_bars[-1]
    indicators_by_time = {_iso(row.snapshot_time): row for row in indicators}
    evidence_label = "provider preview bars" if provider_preview_used else "stored bars"
    evidence_detail = (
        "yfinance preview rows are available but not yet persisted."
        if provider_preview_used
        else "DB-backed OHLCV rows are available."
    )
    freshness_note = (
        "Subscribe the symbol or run System Ops market refresh to persist it."
        if provider_preview_used
        else "Freshness depends on the latest System Ops refresh and indicator calculation."
    )
    payload.judgment = judgment(
        f"SYMBOL JUDGMENT · {ticker}",
        _trend_title(latest_indicator),
        "from Symbol Evidence",
        f"{ticker} has {len(bars)} {timeframe} {evidence_label}.",
        76 if latest_indicator is not None else 58,
    )
    payload.drivers = drivers(
        (str(len(bars)), evidence_label.title(), evidence_detail),
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
            "Symbol bars vs streaming feed",
            "The chart reflects a stored or previewed snapshot, not a streaming quote feed.",
        ),
        (
            "Symbol context vs portfolio context",
            "A symbol can look technically constructive while position constraints remain active.",
        ),
    )
    payload.integrated_interpretation = interpretation(
        "Symbol Lab is reading symbol evidence without exposing execution controls.",
        (
            "Stored bars and indicators make the ticker inspectable from the local DB."
            if not provider_preview_used
            else (
                "Provider preview makes an arbitrary searched ticker inspectable "
                "before subscription."
            )
        ),
        freshness_note,
    )
    payload.review_watchpoints = watchpoints(
        ("Refresh timestamp", "Check /api/system-status for latest market bar time."),
        ("Position context", "Review active alerts if this symbol is currently held."),
        (
            "Symbol logo",
            "Logo metadata uses the configured provider cache when available.",
        ),
    )
    payload.header = SymbolLabHeader(
        ticker=ticker,
        timeframe=timeframe,
        latest_close=latest_bar.close,
        latest_time=_iso(latest_bar.bar_time),
        data_status="OK" if latest_indicator is not None else "PARTIAL",
    )
    payload.data_state = _data_state_for(
        chart_status=payload.header.data_status,
        chart_evidence="provider_preview" if provider_preview_used else "stored",
        bars=bars,
        latest_indicator=latest_indicator,
        identity=payload.identity,
        subscription=payload.subscription,
        provider_note=provider_note,
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
            ema_20=getattr(indicators_by_time.get(_iso(bar.bar_time)), "ema_20", None),
            ema_60=getattr(indicators_by_time.get(_iso(bar.bar_time)), "ema_60", None),
            ema_120=getattr(
                indicators_by_time.get(_iso(bar.bar_time)), "ema_120", None
            ),
            bb_mid=getattr(indicators_by_time.get(_iso(bar.bar_time)), "bb_mid", None),
            bb_upper=getattr(
                indicators_by_time.get(_iso(bar.bar_time)), "bb_upper", None
            ),
            bb_lower=getattr(
                indicators_by_time.get(_iso(bar.bar_time)), "bb_lower", None
            ),
        )
        for bar in visible_bars
    ]
    payload.watchpoints = [
        "Symbol bars are snapshots, not a streaming quote feed.",
        "Recompute indicators after refreshing market bars for full context.",
        "Ticker logos are resolved from cached provider metadata when configured.",
    ]
    if provider_preview_used:
        payload.watchpoints.append(
            "Subscribe the ticker to include it in the local refresh universe."
        )
    if position is not None and position.market_value > SINGLE_POSITION_REVIEW_THRESHOLD:
        payload.watchpoints.append(
            "Position value is above the configured single-position review threshold."
        )
    payload.interpretation = (
        f"{ticker} symbol context is based on {len(bars)} {evidence_label}. "
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


def _prefer_provider_bars(bars: list) -> list:
    if not bars:
        return bars
    provider_rows = [bar for bar in bars if getattr(bar, "source", None) != "mock"]
    return provider_rows or bars


def _bars_for_timeframe_window(bars: list, timeframe: str) -> list:
    if not bars:
        return bars
    latest = max(_as_utc(bar.bar_time) for bar in bars)
    days_by_timeframe = {
        "5m": 7,
        "15m": 35,
        "1h": 75,
        "1d": 370,
    }
    days = days_by_timeframe.get(timeframe)
    if days is None:
        return bars
    cutoff = latest - timedelta(days=days)
    return [bar for bar in bars if _as_utc(bar.bar_time) >= cutoff]


def _indicators_for_bars(indicators: list, bars: list) -> list:
    if not indicators or not bars:
        return indicators
    bar_times = {_as_utc(bar.bar_time) for bar in bars}
    return [
        indicator
        for indicator in indicators
        if _as_utc(indicator.snapshot_time) in bar_times
    ]


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


def _live_symbol_news(session, ticker: str) -> list[SymbolNewsItem]:
    """Stored news impacts linked to this ticker (the same pipeline the News
    Intelligence tab reads). Empty when nothing is linked — no fixture rows."""

    from finskillos.services.news_service import NewsService

    symbol = (ticker or "").strip().upper()
    # Side-rail summary — the dedicated News tab carries the full list, so cap the
    # most-recent items here to keep the panel compact.
    rows = NewsService(session).list_articles_for_ticker(symbol, limit=5)
    items: list[SymbolNewsItem] = []
    for article, impacts in rows:
        # Use the impact scored for this ticker (else the strongest) for the
        # sentiment / score / risk note attached to the headline.
        relevant = [i for i in impacts if (i.ticker or "").upper() == symbol] or list(
            impacts
        )
        lead = max(relevant, key=lambda i: i.impact_score) if relevant else None
        items.append(
            SymbolNewsItem(
                title=article.title,
                source=article.source,
                published_at=article.published_at.isoformat()
                if article.published_at
                else "",
                sentiment_label=lead.sentiment_label if lead else "UNKNOWN",
                impact_score=lead.impact_score if lead else Decimal("0"),
                risk_note=lead.risk_note if lead else None,
                url=article.url,
            )
        )
    return items


def _live_regime_context(session, bars: list) -> RegimeContext | None:
    """Build the Symbol Lab regime card from the latest stored market regime.

    Market-wide (the same regime the Control Room reads). ``freshness`` is STALE
    when newer price bars exist than the regime was computed from. Returns None
    when no regime row is stored so the panel renders its empty state rather than
    leaking the fixture's sample regime."""

    from finskillos.ui.view_models.control_room_vm import _build_regime_summary

    summary = _build_regime_summary(session)
    if summary is None:
        return None
    snapshot = summary.snapshot_time
    latest_bar_time = _as_utc(bars[-1].bar_time) if bars else None
    if snapshot is None or latest_bar_time is None:
        freshness = "UNKNOWN"
    else:
        freshness = "STALE" if latest_bar_time > _as_utc(snapshot) else "FRESH"
    return RegimeContext(
        regime=summary.regime,
        confidence=summary.confidence,
        decision_mode=summary.decision_mode,
        risk_level=summary.risk_level,
        summary=summary.summary,
        what_happened=summary.what_happened,
        what_it_means=summary.what_it_means,
        positive_factors=list(summary.positive_factors),
        risk_factors=list(summary.risk_factors),
        watch_next=list(summary.watch_next),
        snapshot_time=snapshot.isoformat() if snapshot else None,
        freshness=freshness,
        attribution=[],
        confidence_rationale=_regime_confidence_rationale(summary),
    )


def _regime_confidence_rationale(summary) -> str:
    """One descriptive line on the confidence band + supporting/opposing counts.
    Mirrors the Analysis Workspace rationale; derived only from stored values."""

    confidence = summary.confidence
    supporting = len(summary.positive_factors)
    opposing = len(summary.risk_factors)
    if confidence >= 70:
        band = "High confidence"
    elif confidence >= 40:
        band = "Moderate confidence"
    else:
        band = "Low confidence"
    return (
        f"{band} ({int(confidence)}/100) — {supporting} supporting vs {opposing} "
        "opposing factor(s) in the stored rule rationale."
    )


def _fallback_indicators_from_bars(
    ticker: str,
    timeframe: str,
    bars: list,
) -> list[IndicatorSnapshotDTO]:
    closes = [bar.close for bar in bars]
    volumes = [bar.volume if bar.volume is not None else Decimal("0") for bar in bars]
    rsi14 = technical.rsi(closes, period=14)
    ema20 = technical.ema(closes, period=20)
    ema60 = technical.ema(closes, period=60)
    ema120 = technical.ema(closes, period=120)
    bands = technical.bollinger(closes, period=20)
    vol_z = technical.volume_zscore(volumes, period=20)
    momentum = technical.momentum_score(closes, period=20)

    snapshots: list[IndicatorSnapshotDTO] = []
    for index, bar in enumerate(bars):
        bb_mid, bb_upper, bb_lower = bands[index]
        snapshots.append(
            IndicatorSnapshotDTO(
                ticker=ticker,
                timeframe=timeframe,
                snapshot_time=bar.bar_time,
                rsi_14=rsi14[index],
                ema_20=ema20[index],
                ema_60=ema60[index],
                ema_120=ema120[index],
                bb_mid=bb_mid,
                bb_upper=bb_upper,
                bb_lower=bb_lower,
                volume_zscore=vol_z[index],
                momentum_score=momentum[index],
                trend_state=technical.trend_state(
                    bar.close,
                    ema20[index],
                    ema60[index],
                    ema120[index],
                ),
                source="chart_fallback",
            )
        )
    return snapshots


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


def _symbol_identity(session, ticker: str) -> SymbolIdentity:
    fallback = symbol_identity(ticker)
    resolved = resolve_symbol_logo_identity(
        session,
        ticker=fallback.ticker,
        name=fallback.name,
        avatar_text=fallback.avatar_text,
        brand_color=fallback.brand_color,
    )
    return SymbolIdentity(
        ticker=resolved.ticker,
        name=resolved.name,
        logo_url=resolved.logo_url,
        logo_source=resolved.logo_source,
        avatar_text=resolved.avatar_text,
        brand_color=resolved.brand_color,
    )


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


def _subscription_state(subscription) -> SymbolSubscriptionState:
    active = bool(subscription and subscription.active)
    last_action = "subscribed" if active else "unsubscribed" if subscription else "none"
    return SymbolSubscriptionState(
        is_subscribed=active,
        can_subscribe=True,
        update_universe_member=active,
        last_action=last_action,
    )


def _data_state_for(
    *,
    chart_status: str,
    chart_evidence: str,
    bars: list,
    latest_indicator,
    identity: SymbolIdentity,
    subscription: SymbolSubscriptionState,
    provider_note: str | None,
) -> SymbolLabDataState:
    if latest_indicator is not None:
        indicator_status = "AVAILABLE"
    elif bars:
        indicator_status = "PARTIAL"
    else:
        indicator_status = "MISSING"

    if not subscription.can_subscribe:
        subscription_status = "unavailable"
    elif subscription.is_subscribed:
        subscription_status = "subscribed"
    else:
        subscription_status = "watch_only"

    coverage_level = cov.coverage_level(
        bar_count=len(bars),
        indicator_status=indicator_status,
    )

    return SymbolLabDataState(
        chart_status=chart_status,
        chart_evidence=chart_evidence,
        bar_count=len(bars),
        coverage_level=coverage_level,
        evidence_coverage_percent=cov.evidence_coverage_percent(
            bar_count=len(bars),
            indicator_status=indicator_status,
        ),
        missing_summary=cov.missing_summary(
            domain="symbol-lab",
            ticker=identity.ticker,
            bar_count=len(bars),
            coverage_level=coverage_level,
            indicator_status=indicator_status,
        ),
        indicator_status=indicator_status,
        logo_source=identity.logo_source,
        subscription_status=subscription_status,
        provider_note=provider_note,
    )


def _folder_schema(folder) -> SymbolSubscriptionFolder:
    return SymbolSubscriptionFolder(
        id=str(folder.id),
        name=folder.name,
        description=folder.description,
        sort_order=folder.sort_order,
        members=[
            SymbolSubscriptionFolderMember(ticker=member.ticker, name=member.name)
            for member in folder.members
        ],
    )


def _get_subscription_safe(session, ticker: str):
    try:
        return SymbolSubscriptionRepository(session).get(ticker)
    except Exception:
        session.rollback()
        return None


def _refresh_subscribed_symbol(session, ticker: str) -> None:
    adapter_name = os.environ.get("FINSKILLOS_SYMBOL_SUBSCRIBE_ADAPTER", "yahoo").lower()
    if adapter_name == "off":
        return
    adapter = _symbol_market_adapter(adapter_name)
    service = MarketDataService(session, adapter=adapter, universe=[ticker])
    service.refresh_bars([ticker], end=datetime.now(tz=UTC))
    SignalService(session).compute_for_universe([ticker])


def _refresh_symbol_chart_data(session, ticker: str, timeframe: str) -> str | None:
    adapter_name = _symbol_auto_refresh_adapter_name()
    if adapter_name == "off":
        return None
    try:
        service = MarketDataService(
            session,
            adapter=_symbol_market_adapter(adapter_name),
            universe=[ticker],
        )
        report = service.refresh_bars(
            [ticker],
            timeframe=timeframe,
            end=datetime.now(tz=UTC),
            force_full=timeframe in {"1mo", "1y"},
        )
        if report.total_bars_written:
            SignalService(session).compute_for_universe(
                [ticker],
                timeframe=timeframe,
                persist_history=True,
            )
        if report.failed:
            return _provider_note_text(report.failed[0].error)
    except Exception as exc:  # noqa: BLE001 - provider boundary should not blank UI
        session.rollback()
        return _provider_note_text(f"{type(exc).__name__}: {exc}")
    return None


def _symbol_market_adapter(adapter_name: str):
    if adapter_name == "mock":
        return MockMarketDataAdapter()
    if adapter_name == "yahoo":
        return YahooChartMarketDataAdapter()
    raise MarketDataFetchError(f"unsupported symbol market adapter: {adapter_name}")


def _symbol_auto_refresh_adapter_name() -> str:
    return os.environ.get(
        "FINSKILLOS_SYMBOL_AUTO_REFRESH_ADAPTER",
        os.environ.get("FINSKILLOS_SYMBOL_PREVIEW_ADAPTER", "yahoo"),
    ).lower()


def _symbol_preview_enabled() -> bool:
    return os.environ.get("FINSKILLOS_SYMBOL_PREVIEW_ADAPTER", "yahoo").lower() != "off"


def _provider_note(exc: MarketDataFetchError) -> str:
    return _provider_note_text(str(exc).strip() or exc.__class__.__name__)


def _provider_note_text(value: str | None) -> str:
    text = (value or "").strip() or "provider refresh failed"
    return text[:160]


def _missing_symbol_setup_hint(ticker: str, provider_note: str | None) -> str:
    base = (
        f"Run System Ops -> Refresh market bars with {ticker} in "
        "FINSKILLOS_MARKET_REFRESH_TICKERS, or subscribe the symbol to add it "
        "to the local refresh universe."
    )
    if not provider_note:
        return base
    return (
        f"{base} yfinance preview also failed for this request: {provider_note}."
    )


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


def _normalize_timeframe(timeframe: str | None) -> str:
    normalized = (timeframe or DEFAULT_TIMEFRAME).strip().lower()
    normalized = TIMEFRAME_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_SYMBOL_TIMEFRAMES:
        return DEFAULT_TIMEFRAME
    return normalized




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
