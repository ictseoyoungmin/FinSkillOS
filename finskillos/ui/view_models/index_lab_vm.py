"""Slice 08 — Analysis Workspace / Index Lab view-model assembly.

Pure read-model for the Index Lab page. Reads ``market_bars`` and
``indicator_snapshots`` for a fixed US-market index / ETF / macro
universe plus the latest ``MarketRegime`` row, then composes a
deterministic ``IndexLabViewModel`` the Streamlit page can render
without any service-layer access.

Outputs stay interpretation-first: ``trend_state``, ``data_status``,
``watchpoints``, ``relative_strength_score``. The view model never
emits buy/sell directives — ``assert_index_lab_view_model_is_safe``
re-uses the hardened guard safety regex to enforce that constraint at
the UI seam.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.guards.base import GuardResult, assert_no_forbidden_wording
from finskillos.ui.view_models.control_room_vm import RegimeSummary, _as_utc

UTC = timezone.utc


# ---------------------------------------------------------------------------
# Universe definition
# ---------------------------------------------------------------------------

KIND_INDEX_ETF = "INDEX_ETF"
KIND_SECTOR_ETF = "SECTOR_ETF"
KIND_MACRO_PROXY = "MACRO_PROXY"


@dataclass(frozen=True)
class IndexUniverseEntry:
    ticker: str
    label: str
    kind: str


DEFAULT_INDEX_UNIVERSE: tuple[IndexUniverseEntry, ...] = (
    IndexUniverseEntry("SPY", "S&P 500 ETF", KIND_INDEX_ETF),
    IndexUniverseEntry("QQQ", "Nasdaq 100 ETF", KIND_INDEX_ETF),
    IndexUniverseEntry("DIA", "Dow 30 ETF", KIND_INDEX_ETF),
    IndexUniverseEntry("IWM", "Russell 2000 ETF", KIND_INDEX_ETF),
    IndexUniverseEntry("SMH", "Semiconductor ETF", KIND_SECTOR_ETF),
    IndexUniverseEntry("SOXX", "Semiconductor ETF (iShares)", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLK", "Technology Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLF", "Financials Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLE", "Energy Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLV", "Health Care Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLI", "Industrials Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLY", "Consumer Discretionary Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLP", "Consumer Staples Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("XLU", "Utilities Sector", KIND_SECTOR_ETF),
    IndexUniverseEntry("VIX", "Volatility Index Proxy", KIND_MACRO_PROXY),
    IndexUniverseEntry("DXY", "US Dollar Index Proxy", KIND_MACRO_PROXY),
    IndexUniverseEntry("US10Y", "10Y Treasury Yield Proxy", KIND_MACRO_PROXY),
)


# ---------------------------------------------------------------------------
# View model dataclasses
# ---------------------------------------------------------------------------

DATA_STATUS_OK = "OK"
DATA_STATUS_PARTIAL = "PARTIAL"
DATA_STATUS_MISSING = "MISSING"


@dataclass(frozen=True)
class IndexInstrumentVM:
    ticker: str
    label: str
    kind: str
    latest_close: Decimal | None
    latest_time: datetime | None
    rsi_14: Decimal | None
    ema_20: Decimal | None
    ema_60: Decimal | None
    bb_position: Decimal | None
    volume_z_score: Decimal | None
    momentum_score: Decimal | None
    trend_state: str | None
    data_status: str
    relative_strength_score: Decimal | None
    watchpoints: tuple[str, ...] = ()


@dataclass(frozen=True)
class IndexLabViewModel:
    generated_at: datetime
    timeframe: str
    universe: tuple[IndexInstrumentVM, ...]
    regime: RegimeSummary | None
    strongest: tuple[IndexInstrumentVM, ...]
    weakest: tuple[IndexInstrumentVM, ...]
    missing_data: tuple[str, ...]
    setup_hint: str | None = None

    def has_universe(self) -> bool:
        return any(row.data_status != DATA_STATUS_MISSING for row in self.universe)

    def has_regime(self) -> bool:
        return self.regime is not None


# ---------------------------------------------------------------------------
# Ranking / scoring constants
# ---------------------------------------------------------------------------

TREND_SCORE: dict[str, Decimal] = {
    "BULLISH": Decimal("3"),
    "WEAK_BULLISH": Decimal("2"),
    "NEUTRAL": Decimal("1"),
    "WEAK_BEARISH": Decimal("-1"),
    "BEARISH": Decimal("-2"),
}

# Momentum contribution is divided by this so a +20% move adds ~2 points,
# matching the trend-state ladder roughly. Capped at ±3 so a single
# outlier indicator cannot dominate the score.
_MOMENTUM_DIVISOR = Decimal("10")
_MOMENTUM_CAP = Decimal("3")

_RSI_CONSTRUCTIVE_LOW = Decimal("40")
_RSI_CONSTRUCTIVE_HIGH = Decimal("65")
_RSI_OVERHEAT = Decimal("75")
_RSI_ELEVATED = Decimal("70")
_RSI_OVERSOLD = Decimal("30")

_VOLUME_Z_ELEVATED = Decimal("2")

_STRONGEST_LIMIT = 3
_WEAKEST_LIMIT = 3


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_index_lab_view_model(
    session: Session,
    *,
    universe: Iterable[IndexUniverseEntry] | None = None,
    timeframe: str = DEFAULT_TIMEFRAME,
    generated_at: datetime | None = None,
) -> IndexLabViewModel:
    """Assemble the Index Lab view model from stored bars + indicators.

    Missing data is *tolerated*: tickers without a bar / snapshot get a
    ``DATA_STATUS_MISSING`` row and are surfaced in ``missing_data`` so
    the page can render a clear empty state without crashing.
    """

    now = generated_at or datetime.now(tz=UTC)
    entries = tuple(universe) if universe is not None else DEFAULT_INDEX_UNIVERSE

    market_repo = MarketRepository(session)
    indicator_repo = IndicatorRepository(session)
    regime_repo = MarketRegimeRepository(session)

    rows: list[IndexInstrumentVM] = []
    missing: list[str] = []
    for entry in entries:
        latest_bar = market_repo.latest_bar(entry.ticker, timeframe)
        snapshot = indicator_repo.latest_for(entry.ticker, timeframe)
        row = _build_instrument_row(entry, latest_bar=latest_bar, snapshot=snapshot)
        rows.append(row)
        if row.data_status == DATA_STATUS_MISSING:
            missing.append(entry.ticker)

    # Strongest / weakest only meaningful for ranked instruments (skip
    # macro proxies and rows that lack any scoring inputs).
    ranked = tuple(
        r
        for r in rows
        if r.kind != KIND_MACRO_PROXY and r.relative_strength_score is not None
    )
    strongest = tuple(
        sorted(ranked, key=lambda r: r.relative_strength_score or Decimal("0"), reverse=True)
    )[:_STRONGEST_LIMIT]
    weakest = tuple(
        sorted(ranked, key=lambda r: r.relative_strength_score or Decimal("0"))
    )[:_WEAKEST_LIMIT]

    regime = _build_regime_summary(regime_repo)

    setup_hint: str | None = None
    if not any(r.data_status != DATA_STATUS_MISSING for r in rows):
        setup_hint = (
            "지수 / ETF 데이터가 비어 있습니다. System Ops에서 'Market Refresh' "
            "또는 'Indicators 재계산'을 먼저 실행하세요."
        )

    return IndexLabViewModel(
        generated_at=now,
        timeframe=timeframe,
        universe=tuple(rows),
        regime=regime,
        strongest=strongest,
        weakest=weakest,
        missing_data=tuple(missing),
        setup_hint=setup_hint,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_instrument_row(
    entry: IndexUniverseEntry,
    *,
    latest_bar,
    snapshot,
) -> IndexInstrumentVM:
    latest_close = latest_bar.close if latest_bar is not None else None
    latest_time = _as_utc(latest_bar.bar_time) if latest_bar is not None else None

    rsi_14 = snapshot.rsi_14 if snapshot is not None else None
    ema_20 = snapshot.ema_20 if snapshot is not None else None
    ema_60 = snapshot.ema_60 if snapshot is not None else None
    bb_upper = snapshot.bb_upper if snapshot is not None else None
    bb_lower = snapshot.bb_lower if snapshot is not None else None
    volume_z = snapshot.volume_zscore if snapshot is not None else None
    momentum = snapshot.momentum_score if snapshot is not None else None
    trend_state = snapshot.trend_state if snapshot is not None else None

    bb_position = _bb_position(latest_close, bb_upper=bb_upper, bb_lower=bb_lower)
    data_status = _resolve_data_status(latest_bar=latest_bar, snapshot=snapshot)
    score = _relative_strength_score(
        trend_state=trend_state,
        momentum=momentum,
        rsi_14=rsi_14,
        has_close=latest_close is not None,
        kind=entry.kind,
    )
    watchpoints = _build_watchpoints(
        entry=entry,
        data_status=data_status,
        trend_state=trend_state,
        rsi_14=rsi_14,
        volume_z=volume_z,
    )

    return IndexInstrumentVM(
        ticker=entry.ticker,
        label=entry.label,
        kind=entry.kind,
        latest_close=latest_close,
        latest_time=latest_time,
        rsi_14=rsi_14,
        ema_20=ema_20,
        ema_60=ema_60,
        bb_position=bb_position,
        volume_z_score=volume_z,
        momentum_score=momentum,
        trend_state=trend_state,
        data_status=data_status,
        relative_strength_score=score,
        watchpoints=watchpoints,
    )


def _resolve_data_status(*, latest_bar, snapshot) -> str:
    if latest_bar is None and snapshot is None:
        return DATA_STATUS_MISSING
    if snapshot is None or snapshot.trend_state is None:
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
    position = (close - bb_lower) / band_width
    quant = Decimal("0.0001")
    return position.quantize(quant)


def _relative_strength_score(
    *,
    trend_state: str | None,
    momentum: Decimal | None,
    rsi_14: Decimal | None,
    has_close: bool,
    kind: str,
) -> Decimal | None:
    """Deterministic ranking score; ``None`` for macro proxies or no inputs."""

    if kind == KIND_MACRO_PROXY:
        return None
    if trend_state is None and momentum is None and rsi_14 is None:
        return None

    score = Decimal("0")
    if trend_state is not None and trend_state in TREND_SCORE:
        score += TREND_SCORE[trend_state]

    if momentum is not None:
        contribution = momentum / _MOMENTUM_DIVISOR
        if contribution > _MOMENTUM_CAP:
            contribution = _MOMENTUM_CAP
        elif contribution < -_MOMENTUM_CAP:
            contribution = -_MOMENTUM_CAP
        score += contribution

    if rsi_14 is not None:
        if _RSI_CONSTRUCTIVE_LOW < rsi_14 < _RSI_CONSTRUCTIVE_HIGH:
            score += Decimal("1")
        elif rsi_14 >= _RSI_OVERHEAT:
            score -= Decimal("1")
        elif rsi_14 <= _RSI_OVERSOLD:
            score -= Decimal("1")

    if has_close:
        score += Decimal("0.5")

    quant = Decimal("0.0001")
    return score.quantize(quant)


def _build_watchpoints(
    *,
    entry: IndexUniverseEntry,
    data_status: str,
    trend_state: str | None,
    rsi_14: Decimal | None,
    volume_z: Decimal | None,
) -> tuple[str, ...]:
    notes: list[str] = []

    if data_status == DATA_STATUS_MISSING:
        notes.append("No indicator snapshot is available yet.")
        return tuple(notes)

    if data_status == DATA_STATUS_PARTIAL:
        notes.append("Indicator snapshot is partial; longer-window history may be missing.")

    if rsi_14 is not None:
        if rsi_14 >= _RSI_OVERHEAT:
            notes.append("RSI is overheated; monitor mean-reversion risk.")
        elif rsi_14 >= _RSI_ELEVATED:
            notes.append("RSI is elevated; monitor overheat risk.")
        elif rsi_14 <= _RSI_OVERSOLD:
            notes.append("RSI is depressed; monitor capitulation context.")

    if trend_state == "BEARISH":
        notes.append("Trend state is bearish; treat this as a weak tape signal.")
    elif trend_state == "WEAK_BEARISH":
        notes.append("Trend state is weak bearish; tape strength has faded.")
    elif trend_state == "BULLISH":
        notes.append("Trend state is bullish; tape support is constructive.")

    if volume_z is not None and volume_z >= _VOLUME_Z_ELEVATED:
        notes.append("Volume z-score is elevated; monitor event or rotation context.")

    if entry.kind == KIND_MACRO_PROXY:
        if entry.ticker == "VIX" and trend_state in {"BULLISH", "WEAK_BULLISH"}:
            notes.append("Volatility proxy is rising; macro stress is elevating.")
        elif entry.ticker in {"DXY", "US10Y"} and trend_state in {"BULLISH", "WEAK_BULLISH"}:
            notes.append("Macro pressure proxy is rising; risk-asset headwind is in place.")
        elif entry.ticker == "VIX" and trend_state in {"BEARISH", "WEAK_BEARISH"}:
            notes.append("Volatility proxy is easing; macro stress is fading.")

    return tuple(notes)


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
# Safety scan
# ---------------------------------------------------------------------------


def assert_index_lab_view_model_is_safe(vm: IndexLabViewModel) -> None:
    """Reject any direct-advice wording that may have leaked into the VM.

    Reuses ``assert_no_forbidden_wording`` so the Index Lab page cannot
    surface ``BUY`` / ``SELL`` / ``매수`` / ``매도`` etc. even if a
    downstream regime / indicator field regresses.
    """

    if vm.setup_hint:
        _scan_text(vm.setup_hint, source="setup_hint")

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

    for row in vm.universe:
        _scan_text(row.label, source=f"universe[{row.ticker}].label")
        _scan_text(row.data_status, source=f"universe[{row.ticker}].data_status")
        if row.trend_state is not None:
            _scan_text(row.trend_state, source=f"universe[{row.ticker}].trend_state")
        for note in row.watchpoints:
            _scan_text(note, source=f"universe[{row.ticker}].watchpoints")


def _scan_text(text: str, *, source: str) -> None:
    placeholder = GuardResult(
        guard_name=f"INDEX_LAB:{source}",
        status="INFO",
        risk_level="GREEN",
        title="",
        message=text,
    )
    assert_no_forbidden_wording(placeholder)
