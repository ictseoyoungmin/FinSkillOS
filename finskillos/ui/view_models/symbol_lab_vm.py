"""Slice 09 — Symbol Lab view-model assembly.

Pure read-model for the Symbol Lab page. Reads ``market_bars`` /
``indicator_snapshots`` / ``positions`` / ``portfolio_snapshots`` /
``alerts`` / ``market_regimes`` for a single ticker and composes a
deterministic ``SymbolLabViewModel`` the Streamlit page can render
without any service-layer access.

Outputs stay interpretation-first: ``trend_state``, ``watchpoints``,
``interpretation``. The view model never emits buy/sell directives —
``assert_symbol_lab_view_model_is_safe`` re-uses the hardened guard
safety regex to enforce that constraint at the UI seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.db.models import Alert, Position
from finskillos.db.repositories import (
    AccountRepository,
    AlertRepository,
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
    PortfolioRepository,
    PositionRepository,
)
from finskillos.guards.base import (
    DEFAULT_SINGLE_POSITION_LIMIT_KRW,
    GuardResult,
    assert_no_forbidden_wording,
)
from finskillos.ui.view_models.control_room_vm import RegimeSummary, _as_utc

UTC = timezone.utc

DEFAULT_TICKER = "TSLA"
_RECENT_BARS_LIMIT = 20

DATA_STATUS_OK = "OK"
DATA_STATUS_PARTIAL = "PARTIAL"
DATA_STATUS_MISSING = "MISSING"

_RSI_OVERHEAT = Decimal("75")
_RSI_ELEVATED = Decimal("70")
_RSI_OVERSOLD = Decimal("30")
_VOLUME_Z_ELEVATED = Decimal("2")


# ---------------------------------------------------------------------------
# View model dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SymbolTechnicalVM:
    ticker: str
    latest_close: Decimal | None
    latest_time: datetime | None
    rsi_14: Decimal | None
    ema_20: Decimal | None
    ema_60: Decimal | None
    ema_120: Decimal | None
    bb_position: Decimal | None
    volume_z_score: Decimal | None
    momentum_score: Decimal | None
    trend_state: str | None
    data_status: str


@dataclass(frozen=True)
class SymbolRecentBarVM:
    bar_time: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: Decimal | None


@dataclass(frozen=True)
class SymbolPositionVM:
    ticker: str
    sector: str | None
    theme: str | None
    strategy_type: str | None
    market_value: Decimal | None
    portfolio_weight: Decimal | None
    pnl_pct: Decimal | None
    quantity: Decimal | None
    thesis: str | None
    over_single_position_limit: bool


@dataclass(frozen=True)
class SymbolAlertVM:
    guard_name: str
    severity: str
    title: str
    message: str
    alert_date: date


@dataclass(frozen=True)
class SymbolLabViewModel:
    ticker: str
    generated_at: datetime
    timeframe: str
    technical: SymbolTechnicalVM
    recent_bars: tuple[SymbolRecentBarVM, ...]
    position: SymbolPositionVM | None
    alerts: tuple[SymbolAlertVM, ...]
    regime: RegimeSummary | None
    watchpoints: tuple[str, ...]
    interpretation: str
    setup_hint: str | None = None

    def has_position(self) -> bool:
        return self.position is not None

    def has_technical_data(self) -> bool:
        return self.technical.data_status != DATA_STATUS_MISSING

    def has_recent_bars(self) -> bool:
        return bool(self.recent_bars)

    def has_regime(self) -> bool:
        return self.regime is not None

    def has_alerts(self) -> bool:
        return bool(self.alerts)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def normalize_ticker(raw: str | None) -> str:
    """Normalize a user-entered ticker to uppercase + stripped."""

    if raw is None:
        return ""
    return raw.strip().upper()


def build_symbol_lab_view_model(
    session: Session,
    *,
    ticker: str | None = None,
    timeframe: str = DEFAULT_TIMEFRAME,
    account_name: str | None = None,
    generated_at: datetime | None = None,
) -> SymbolLabViewModel:
    """Assemble the Symbol Lab view model for one ticker.

    Missing data is *tolerated*: any of the underlying stores can be
    empty without crashing the page. The page only needs to inspect
    ``has_technical_data`` / ``has_position`` / ``setup_hint`` to
    decide what to render.
    """

    now = generated_at or datetime.now(tz=UTC)
    resolved_ticker, default_source = _resolve_default_ticker(
        session, requested=ticker, account_name=account_name
    )

    market_repo = MarketRepository(session)
    indicator_repo = IndicatorRepository(session)
    regime_repo = MarketRegimeRepository(session)
    alert_repo = AlertRepository(session)

    technical = _build_technical(
        market_repo=market_repo,
        indicator_repo=indicator_repo,
        ticker=resolved_ticker,
        timeframe=timeframe,
    )
    recent_bars = _build_recent_bars(
        market_repo=market_repo, ticker=resolved_ticker, timeframe=timeframe
    )

    account = _resolve_account(session, account_name=account_name)
    position_vm: SymbolPositionVM | None = None
    if account is not None and resolved_ticker:
        position_vm = _build_position(
            session=session,
            account_id=account.id,
            ticker=resolved_ticker,
        )

    alerts = _build_alerts(
        alert_repo=alert_repo,
        account_id=account.id if account is not None else None,
        ticker=resolved_ticker,
    )
    regime = _build_regime_summary(regime_repo)

    watchpoints = _build_watchpoints(
        ticker=resolved_ticker,
        technical=technical,
        position=position_vm,
    )
    interpretation = _build_interpretation(
        ticker=resolved_ticker,
        technical=technical,
        position=position_vm,
        regime=regime,
    )
    setup_hint = _build_setup_hint(
        requested=ticker,
        resolved_ticker=resolved_ticker,
        default_source=default_source,
        technical=technical,
    )

    return SymbolLabViewModel(
        ticker=resolved_ticker,
        generated_at=now,
        timeframe=timeframe,
        technical=technical,
        recent_bars=recent_bars,
        position=position_vm,
        alerts=alerts,
        regime=regime,
        watchpoints=watchpoints,
        interpretation=interpretation,
        setup_hint=setup_hint,
    )


# ---------------------------------------------------------------------------
# Private helpers — defaulting + technical context
# ---------------------------------------------------------------------------


def _resolve_default_ticker(
    session: Session,
    *,
    requested: str | None,
    account_name: str | None,
) -> tuple[str, str]:
    """Return (ticker, source) where source is 'user' / 'position' / 'fallback' / 'empty'."""

    normalized = normalize_ticker(requested)
    if normalized:
        return normalized, "user"

    account = _resolve_account(session, account_name=account_name)
    if account is not None:
        positions = PositionRepository(session).list_for_account(account.id)
        if positions:
            return positions[0].ticker.upper(), "position"

    return DEFAULT_TICKER, "fallback"


def _resolve_account(session: Session, *, account_name: str | None):
    accounts = AccountRepository(session)
    if account_name is not None:
        return accounts.get_by_name(account_name)
    rows = accounts.list_all()
    return rows[0] if rows else None


def _build_technical(
    *,
    market_repo: MarketRepository,
    indicator_repo: IndicatorRepository,
    ticker: str,
    timeframe: str,
) -> SymbolTechnicalVM:
    if not ticker:
        return SymbolTechnicalVM(
            ticker="",
            latest_close=None,
            latest_time=None,
            rsi_14=None,
            ema_20=None,
            ema_60=None,
            ema_120=None,
            bb_position=None,
            volume_z_score=None,
            momentum_score=None,
            trend_state=None,
            data_status=DATA_STATUS_MISSING,
        )

    latest_bar = market_repo.latest_bar(ticker, timeframe)
    snapshot = indicator_repo.latest_for(ticker, timeframe)

    latest_close = latest_bar.close if latest_bar is not None else None
    latest_time = _as_utc(latest_bar.bar_time) if latest_bar is not None else None
    bb_position = _bb_position(
        latest_close,
        bb_upper=snapshot.bb_upper if snapshot is not None else None,
        bb_lower=snapshot.bb_lower if snapshot is not None else None,
    )

    return SymbolTechnicalVM(
        ticker=ticker,
        latest_close=latest_close,
        latest_time=latest_time,
        rsi_14=snapshot.rsi_14 if snapshot is not None else None,
        ema_20=snapshot.ema_20 if snapshot is not None else None,
        ema_60=snapshot.ema_60 if snapshot is not None else None,
        ema_120=snapshot.ema_120 if snapshot is not None else None,
        bb_position=bb_position,
        volume_z_score=snapshot.volume_zscore if snapshot is not None else None,
        momentum_score=snapshot.momentum_score if snapshot is not None else None,
        trend_state=snapshot.trend_state if snapshot is not None else None,
        data_status=_resolve_data_status(latest_bar=latest_bar, snapshot=snapshot),
    )


def _build_recent_bars(
    *,
    market_repo: MarketRepository,
    ticker: str,
    timeframe: str,
) -> tuple[SymbolRecentBarVM, ...]:
    if not ticker:
        return ()
    bars = market_repo.list_bars(ticker, timeframe)
    if not bars:
        return ()
    # ``list_bars`` returns ascending order; we want the most recent
    # ``_RECENT_BARS_LIMIT`` rows, still ascending so a chart-data
    # transformer can pass them straight to a candlestick renderer.
    tail = bars[-_RECENT_BARS_LIMIT:]
    return tuple(
        SymbolRecentBarVM(
            bar_time=_as_utc(bar.bar_time),
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in tail
    )


def _resolve_data_status(*, latest_bar, snapshot) -> str:
    if latest_bar is None and snapshot is None:
        return DATA_STATUS_MISSING
    if latest_bar is None or snapshot is None or snapshot.trend_state is None:
        return DATA_STATUS_PARTIAL
    return DATA_STATUS_OK


def _bb_position(
    close: Decimal | None,
    *,
    bb_upper: Decimal | None,
    bb_lower: Decimal | None,
) -> Decimal | None:
    if close is None or bb_upper is None or bb_lower is None:
        return None
    band_width = bb_upper - bb_lower
    if band_width <= 0:
        return None
    quant = Decimal("0.0001")
    return ((close - bb_lower) / band_width).quantize(quant)


# ---------------------------------------------------------------------------
# Position + portfolio context
# ---------------------------------------------------------------------------


def _build_position(
    *,
    session: Session,
    account_id,
    ticker: str,
) -> SymbolPositionVM | None:
    position = PositionRepository(session).get_by_account_and_ticker(account_id, ticker)
    if position is None:
        return None

    weight = _portfolio_weight(session=session, account_id=account_id, position=position)
    over_limit = (
        position.market_value is not None
        and position.market_value > DEFAULT_SINGLE_POSITION_LIMIT_KRW
    )

    return SymbolPositionVM(
        ticker=position.ticker,
        sector=position.sector,
        theme=position.theme,
        strategy_type=position.strategy_type,
        market_value=position.market_value,
        portfolio_weight=weight,
        pnl_pct=position.pnl_pct,
        quantity=position.quantity,
        thesis=position.thesis,
        over_single_position_limit=over_limit,
    )


def _portfolio_weight(
    *,
    session: Session,
    account_id,
    position: Position,
) -> Decimal | None:
    snapshot = PortfolioRepository(session).latest(account_id)
    if snapshot is None or snapshot.total_value is None:
        return None
    total = snapshot.total_value
    if total <= 0 or position.market_value is None:
        return None
    quant = Decimal("0.0001")
    return (position.market_value / total).quantize(quant)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def _build_alerts(
    *,
    alert_repo: AlertRepository,
    account_id,
    ticker: str,
) -> tuple[SymbolAlertVM, ...]:
    if not ticker:
        return ()
    rows = alert_repo.list_active(account_id=account_id)
    matched = [row for row in rows if _alert_mentions_ticker(row, ticker)]
    return tuple(
        SymbolAlertVM(
            guard_name=row.guard_name,
            severity=row.severity,
            title=row.title,
            message=row.message or "",
            alert_date=row.alert_date,
        )
        for row in matched
    )


def _alert_mentions_ticker(alert: Alert, ticker: str) -> bool:
    upper = ticker.upper()
    payload = alert.payload or {}
    if isinstance(payload, dict):
        payload_ticker = payload.get("ticker")
        if isinstance(payload_ticker, str) and payload_ticker.upper() == upper:
            return True
        tickers = payload.get("tickers")
        if isinstance(tickers, (list, tuple)):
            if any(isinstance(t, str) and t.upper() == upper for t in tickers):
                return True
    title = alert.title or ""
    message = alert.message or ""
    return upper in title.upper() or upper in message.upper()


# ---------------------------------------------------------------------------
# Regime
# ---------------------------------------------------------------------------


def _build_regime_summary(regime_repo: MarketRegimeRepository) -> RegimeSummary | None:
    latest = regime_repo.latest()
    if latest is None:
        return None
    return RegimeSummary(
        regime=latest.regime,
        confidence=latest.confidence,
        decision_mode=latest.decision_mode,
        risk_level=latest.risk_level,
        summary=latest.summary or "",
        what_happened=latest.what_happened or "",
        what_it_means=latest.what_it_means or "",
        positive_factors=tuple(latest.positive_factors or ()),
        risk_factors=tuple(latest.risk_factors or ()),
        watch_next=tuple(latest.watch_next or ()),
        snapshot_time=_as_utc(latest.snapshot_time),
    )


# ---------------------------------------------------------------------------
# Watchpoints + interpretation
# ---------------------------------------------------------------------------


def _build_watchpoints(
    *,
    ticker: str,
    technical: SymbolTechnicalVM,
    position: SymbolPositionVM | None,
) -> tuple[str, ...]:
    notes: list[str] = []

    if technical.data_status == DATA_STATUS_MISSING:
        notes.append(
            f"No stored market bar or indicator snapshot exists for {ticker}."
        )
    elif technical.data_status == DATA_STATUS_PARTIAL:
        notes.append(
            f"Stored data for {ticker} is partial; some indicator fields are missing."
        )

    rsi = technical.rsi_14
    if rsi is not None:
        if rsi >= _RSI_OVERHEAT:
            notes.append("RSI is overheated; monitor mean-reversion risk.")
        elif rsi >= _RSI_ELEVATED:
            notes.append("RSI is elevated; monitor short-term overheat risk.")
        elif rsi <= _RSI_OVERSOLD:
            notes.append("RSI is depressed; monitor capitulation context.")

    if technical.trend_state == "BEARISH":
        notes.append("Trend state is bearish; treat this as a weak tape signal.")
    elif technical.trend_state == "WEAK_BEARISH":
        notes.append("Trend state is weak bearish; tape strength has faded.")
    elif technical.trend_state == "BULLISH":
        notes.append("Trend state is bullish; tape support is constructive.")

    if (
        technical.volume_z_score is not None
        and technical.volume_z_score >= _VOLUME_Z_ELEVATED
    ):
        notes.append("Volume z-score is elevated; monitor event or rotation context.")

    if position is not None:
        if position.over_single_position_limit:
            notes.append(
                "Position value is above the configured single-position limit; "
                "review sizing before adding risk."
            )
        if position.pnl_pct is not None and position.pnl_pct <= Decimal("-10"):
            notes.append(
                "Open P&L is deeply negative; review thesis and stop-reference notes."
            )

    return tuple(notes)


def _build_interpretation(
    *,
    ticker: str,
    technical: SymbolTechnicalVM,
    position: SymbolPositionVM | None,
    regime: RegimeSummary | None,
) -> str:
    if not ticker:
        return (
            "Enter a ticker to load its stored market bars, indicators, "
            "and any related position context."
        )

    sentences: list[str] = []

    if technical.data_status == DATA_STATUS_MISSING:
        sentences.append(
            f"{ticker} has no stored market bars or indicator snapshots yet."
        )
    else:
        trend_label = technical.trend_state or "unclassified"
        rsi_label = (
            f"RSI(14) at {technical.rsi_14.quantize(Decimal('0.1'))}"
            if technical.rsi_14 is not None
            else "RSI is not yet available"
        )
        sentences.append(
            f"{ticker} latest trend state is {trend_label}; {rsi_label}."
        )

    if position is None:
        sentences.append(f"No current holding is recorded for {ticker}.")
    else:
        if position.market_value is not None:
            sentences.append(
                f"Current position market value is "
                f"{position.market_value.quantize(Decimal('1'))} KRW."
            )
        if position.over_single_position_limit:
            sentences.append(
                "Position value is above the configured single-position limit; "
                "review sizing before adding risk."
            )

    if regime is not None:
        sentences.append(
            f"Market regime is {regime.regime} ({regime.decision_mode}); "
            f"risk level {regime.risk_level}."
        )

    return " ".join(sentences)


# ---------------------------------------------------------------------------
# Setup hint
# ---------------------------------------------------------------------------


def _build_setup_hint(
    *,
    requested: str | None,
    resolved_ticker: str,
    default_source: str,
    technical: SymbolTechnicalVM,
) -> str | None:
    requested_normalized = normalize_ticker(requested)
    if requested is not None and not requested_normalized:
        return (
            "ticker를 입력하면 저장된 market_bars / indicator_snapshots / "
            "position 컨텍스트를 종합해 표시합니다."
        )

    if technical.data_status == DATA_STATUS_MISSING:
        return (
            f"{resolved_ticker} 데이터가 비어 있습니다. market_bars / "
            "indicator_snapshots 데이터가 저장되면 이 화면에 표시됩니다. "
            "현재 Slice 09에서는 자동 refresh를 수행하지 않습니다."
        )

    if default_source == "fallback":
        return (
            f"기본 ticker({resolved_ticker})를 사용 중입니다. "
            "검색창에서 다른 ticker를 입력하면 해당 종목으로 전환됩니다."
        )

    return None


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def assert_symbol_lab_view_model_is_safe(vm: SymbolLabViewModel) -> None:
    """Reject any direct-advice wording that may have leaked into the VM.

    Reuses ``assert_no_forbidden_wording`` so the Symbol Lab page cannot
    surface ``BUY`` / ``SELL`` / ``매수`` / ``매도`` etc. even if a
    downstream regime / indicator / alert / position field regresses.
    """

    _scan_text(vm.ticker, source="ticker")
    _scan_text(vm.interpretation, source="interpretation")
    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")

    _scan_text(vm.technical.data_status, source="technical.data_status")
    if vm.technical.trend_state is not None:
        _scan_text(vm.technical.trend_state, source="technical.trend_state")

    for note in vm.watchpoints:
        _scan_text(note, source="watchpoints")

    if vm.position is not None:
        if vm.position.thesis:
            _scan_text(vm.position.thesis, source="position.thesis")
        if vm.position.sector:
            _scan_text(vm.position.sector, source="position.sector")
        if vm.position.theme:
            _scan_text(vm.position.theme, source="position.theme")
        if vm.position.strategy_type:
            _scan_text(vm.position.strategy_type, source="position.strategy_type")

    for alert in vm.alerts:
        _scan_text(alert.title, source="alert.title")
        if alert.message:
            _scan_text(alert.message, source="alert.message")

    if vm.regime is not None:
        _scan_text(vm.regime.summary, source="regime.summary")
        _scan_text(vm.regime.what_happened, source="regime.what_happened")
        _scan_text(vm.regime.what_it_means, source="regime.what_it_means")
        for f in vm.regime.positive_factors:
            _scan_text(f, source="regime.positive_factors")
        for f in vm.regime.risk_factors:
            _scan_text(f, source="regime.risk_factors")
        for f in vm.regime.watch_next:
            _scan_text(f, source="regime.watch_next")


def _scan_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"SYMBOL_LAB:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
