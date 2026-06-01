"""Canonical DTOs for the data-source adapter layer (docs/v2_1/08).

These dataclasses are the *internal* shape every market-data /
indicator producer must emit. Adapters convert from their native
provider responses into these types before anything reaches the
repository or service layer, so the rest of the system never sees a
provider-specific payload.

Slice 04 currently uses `MarketBarDTO` and `IndicatorSnapshotDTO`.
News / event DTOs are intentionally deferred to a later slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

DEFAULT_TIMEFRAME = "1d"

# Slice-04 default US-market focus universe (docs/v2_1/08 §5.1).
# The default refresh universe is the union of every cockpit tab's tickers so a
# single worker refresh populates all of them (no permanently-MISSING rows):
# Analysis Workspace index + sector ETFs, Market Kernel / Symbol Lab mega-caps,
# and the macro proxies.
DEFAULT_US_TICKER_UNIVERSE: tuple[str, ...] = (
    # Index ETFs
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
    # Sector ETFs (+ semis)
    "SMH",
    "SOXX",
    "XLK",
    "XLF",
    "XLE",
    "XLV",
    "XLI",
    "XLY",
    "XLP",
    "XLU",
    # Mega-cap stocks
    "NVDA",
    "TSLA",
    "AAPL",
    "MSFT",
    "AMZN",
    # Macro proxies
    "VIX",
    "US10Y",
    "DXY",
)


@dataclass(frozen=True)
class MarketBarDTO:
    """Canonical OHLCV row used by every market-data adapter.

    `close` is the only non-optional price column because some
    providers (e.g. VIX-style indices) do not always publish a full
    OHLC quartet. `volume` is nullable for the same reason.
    """

    ticker: str
    timeframe: str
    bar_time: datetime
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal
    volume: Decimal | None
    source: str
    adj_close: Decimal | None = None


@dataclass(frozen=True)
class IndicatorSnapshotDTO:
    """Computed indicator block for one (ticker, timeframe, ts) point.

    All numeric fields stay optional so the SignalService can persist a
    partial snapshot when there is not yet enough history for a
    longer-window indicator (EMA120 needs 120 bars).
    """

    ticker: str
    timeframe: str
    snapshot_time: datetime
    rsi_14: Decimal | None = None
    ema_20: Decimal | None = None
    ema_60: Decimal | None = None
    ema_120: Decimal | None = None
    bb_mid: Decimal | None = None
    bb_upper: Decimal | None = None
    bb_lower: Decimal | None = None
    volume_zscore: Decimal | None = None
    momentum_score: Decimal | None = None
    trend_state: str | None = None
    source: str = "internal"
