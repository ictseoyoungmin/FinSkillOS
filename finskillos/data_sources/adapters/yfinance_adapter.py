"""yfinance-backed market-data adapter.

This adapter uses the third-party ``yfinance`` package and normalizes its
``Ticker.history`` DataFrame output into provider-agnostic ``MarketBarDTO``
rows. The rest of FinSkillOS stores canonical OHLCV bars and never depends on
provider-specific column names.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from finskillos.data_sources.dto import MarketBarDTO
from finskillos.data_sources.market_adapter import (
    BaseMarketDataAdapter,
    MarketDataFetchError,
)

UTC = timezone.utc

DEFAULT_YAHOO_SYMBOL_MAP: Mapping[str, str] = {
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
}

TIMEFRAME_TO_YFINANCE_INTERVAL: Mapping[str, str] = {
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "1d": "1d",
    "1wk": "1wk",
    "1w": "1wk",
    "1mo": "1mo",
    "1mon": "1mo",
    "1y": "1mo",
}

DEFAULT_PERIOD_BY_INTERVAL: Mapping[str, str] = {
    "5m": "5d",
    "15m": "1mo",
    "1h": "60d",
    "1d": "1y",
    "1wk": "5y",
    "1mo": "10y",
}


class YahooChartMarketDataAdapter(BaseMarketDataAdapter):
    """Fetch OHLCV bars through ``yfinance.Ticker.history``."""

    source_name = "yfinance"

    def __init__(
        self,
        *,
        symbol_map: Mapping[str, str] | None = None,
        client: Any | None = None,
    ) -> None:
        self.symbol_map = {
            **DEFAULT_YAHOO_SYMBOL_MAP,
            **{k.upper(): v for k, v in (symbol_map or {}).items()},
        }
        self.client = client

    def fetch_bars(
        self,
        ticker: str,
        *,
        timeframe: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[MarketBarDTO]:
        interval = _normalize_interval(timeframe)
        if interval is None:
            raise MarketDataFetchError(
                f"yfinance adapter unsupported timeframe: {timeframe}"
            )

        ticker_upper = ticker.upper()
        yahoo_symbol = self.symbol_map.get(ticker_upper, ticker_upper)
        try:
            history = self._history(
                yahoo_symbol,
                interval=interval,
                start=start,
                end=end,
            )
        except Exception as exc:  # noqa: BLE001 - provider boundary
            raise MarketDataFetchError(
                f"yfinance fetch failed for {ticker_upper}: {exc}"
            ) from exc

        return self._parse_history(
            ticker=ticker_upper,
            timeframe=_canonical_timeframe(timeframe),
            history=history,
        )

    def _history(
        self,
        yahoo_symbol: str,
        *,
        interval: str,
        start: date | datetime | None,
        end: date | datetime | None,
    ) -> Any:
        ticker_obj = self._ticker(yahoo_symbol)
        kwargs: dict[str, Any] = {
            "interval": interval,
            "auto_adjust": False,
            "actions": False,
        }
        if start is None:
            kwargs["period"] = DEFAULT_PERIOD_BY_INTERVAL[interval]
        else:
            kwargs["start"] = start
            if end is not None:
                kwargs["end"] = end
        return ticker_obj.history(**kwargs)

    def _ticker(self, yahoo_symbol: str) -> Any:
        if self.client is not None:
            return self.client.Ticker(yahoo_symbol)

        try:
            import yfinance as yf
        except ImportError as exc:
            raise MarketDataFetchError(
                "yfinance package is not installed; install requirements.txt"
            ) from exc
        return yf.Ticker(yahoo_symbol)

    def _parse_history(
        self,
        *,
        ticker: str,
        timeframe: str,
        history: Any,
    ) -> list[MarketBarDTO]:
        if getattr(history, "empty", False):
            raise MarketDataFetchError(f"yfinance returned no history rows for {ticker}")

        rows = list(history.iterrows()) if hasattr(history, "iterrows") else []
        bars: list[MarketBarDTO] = []
        for raw_index, row in rows:
            close = _decimal_from_row(row, "Close")
            if close is None:
                continue
            bar_time = _datetime_from_index(raw_index)
            if bar_time is None:
                continue
            bars.append(
                MarketBarDTO(
                    ticker=ticker,
                    timeframe=timeframe,
                    bar_time=bar_time,
                    open=_decimal_from_row(row, "Open"),
                    high=_decimal_from_row(row, "High"),
                    low=_decimal_from_row(row, "Low"),
                    close=close,
                    volume=_decimal_from_row(row, "Volume"),
                    adj_close=_decimal_from_row(row, "Adj Close"),
                    source=self.source_name,
                )
            )

        if not bars:
            raise MarketDataFetchError(
                f"yfinance history had no usable close bars for {ticker}"
            )
        bars.sort(key=lambda bar: bar.bar_time)
        return bars


def _normalize_interval(timeframe: str) -> str | None:
    return TIMEFRAME_TO_YFINANCE_INTERVAL.get(timeframe.lower())


def _canonical_timeframe(timeframe: str) -> str:
    value = timeframe.lower()
    if value == "1w":
        return "1wk"
    if value == "1mon":
        return "1mo"
    return value


def _datetime_from_index(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if hasattr(value, "to_pydatetime"):
        as_dt = value.to_pydatetime()
        return as_dt.astimezone(UTC) if as_dt.tzinfo else as_dt.replace(tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _decimal_from_row(row: Any, key: str) -> Decimal | None:
    try:
        raw = row[key]
    except (KeyError, TypeError):
        return None
    if raw is None:
        return None
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
