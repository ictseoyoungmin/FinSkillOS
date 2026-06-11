"""Toss market-data adapter — v4 Phase 16.

Maps Toss candle (OHLCV) data into the canonical ``MarketBarDTO`` so the System
Ops refresh pipeline can use Toss as a market source for KR + US symbols
(alongside the yahoo / mock adapters). Read-only.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from finskillos.data_sources.dto import MarketBarDTO
from finskillos.data_sources.market_adapter import (
    BaseMarketDataAdapter,
    MarketDataFetchError,
)

_INTERVALS = {"1d": "1d", "1m": "1m"}
_MAX_PAGES = 5


def _dec(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


class TossMarketDataAdapter(BaseMarketDataAdapter):
    source_name = "toss"

    def __init__(self, client=None) -> None:
        from finskillos.brokerage.toss.client import TossClient

        self._client = client or TossClient()

    def fetch_bars(
        self,
        ticker: str,
        *,
        timeframe: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[MarketBarDTO]:
        interval = _INTERVALS.get(timeframe)
        if interval is None:
            raise MarketDataFetchError(
                f"toss adapter unsupported timeframe: {timeframe}"
            )
        symbol = ticker.upper()
        bars: list[MarketBarDTO] = []
        before: str | None = None
        for _ in range(_MAX_PAGES):
            page = self._client.candles(symbol, interval=interval, before=before)
            candles = page.get("candles") if isinstance(page, dict) else None
            for candle in candles or []:
                bar = self._to_bar(ticker, timeframe, candle)
                if bar is not None:
                    bars.append(bar)
            before = page.get("nextBefore") if isinstance(page, dict) else None
            if not before:
                break
            if start is not None and bars and _before_start(bars[-1].bar_time, start):
                break
        return _filter_range(bars, start, end)

    def _to_bar(self, ticker: str, timeframe: str, candle: dict) -> MarketBarDTO | None:
        if not isinstance(candle, dict):
            return None
        close = _dec(candle.get("closePrice"))
        ts = candle.get("timestamp")
        if close is None or not ts:
            return None
        try:
            bar_time = datetime.fromisoformat(str(ts))
        except ValueError:
            return None
        return MarketBarDTO(
            ticker=ticker.upper(),
            timeframe=timeframe,
            bar_time=bar_time,
            open=_dec(candle.get("openPrice")),
            high=_dec(candle.get("highPrice")),
            low=_dec(candle.get("lowPrice")),
            close=close,
            volume=_dec(candle.get("volume")),
            source=self.source_name,
        )


def _as_datetime(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime(value.year, value.month, value.day)


def _before_start(bar_time: datetime, start: date | datetime) -> bool:
    s = _as_datetime(start)
    bt = bar_time.replace(tzinfo=None) if bar_time.tzinfo else bar_time
    return bt < s.replace(tzinfo=None) if s.tzinfo else bt < s


def _filter_range(bars, start, end):
    def keep(bar) -> bool:
        bt = bar.bar_time.replace(tzinfo=None) if bar.bar_time.tzinfo else bar.bar_time
        if start is not None and bt < _as_datetime(start).replace(tzinfo=None):
            return False
        if end is not None and bt > _as_datetime(end).replace(tzinfo=None):
            return False
        return True

    return sorted((b for b in bars if keep(b)), key=lambda b: b.bar_time)
