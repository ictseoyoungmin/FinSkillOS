"""Yahoo Chart market-data adapter.

Despite the historical file name, this adapter intentionally avoids a hard
runtime dependency on the third-party ``yfinance`` package. It talks to the
public Yahoo Chart endpoint with ``httpx`` and normalizes the response into
``MarketBarDTO`` so the rest of FinSkillOS stays provider-agnostic.

The adapter is opt-in from refresh scripts. Product API routes should not use
it during request rendering; they read stored DB snapshots instead.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

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

TIMEFRAME_TO_INTERVAL: Mapping[str, str] = {
    "1h": "1h",
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo",
}

DEFAULT_RANGE_BY_TIMEFRAME: Mapping[str, str] = {
    "1h": "60d",
    "1d": "1y",
    "1wk": "5y",
    "1mo": "10y",
}


class YahooChartMarketDataAdapter(BaseMarketDataAdapter):
    """Fetch OHLCV bars from Yahoo Chart API.

    Network/provider failures are converted into ``MarketDataFetchError`` so
    ``MarketDataService`` can preserve per-ticker failure isolation.
    """

    source_name = "yahoo"

    def __init__(
        self,
        *,
        base_url: str = "https://query1.finance.yahoo.com/v8/finance/chart",
        timeout_seconds: float = 20.0,
        symbol_map: Mapping[str, str] | None = None,
        client: Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
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
        interval = TIMEFRAME_TO_INTERVAL.get(timeframe)
        if interval is None:
            raise MarketDataFetchError(f"yahoo adapter unsupported timeframe: {timeframe}")

        ticker_upper = ticker.upper()
        yahoo_symbol = self.symbol_map.get(ticker_upper, ticker_upper)
        params = self._query_params(timeframe=timeframe, interval=interval, start=start, end=end)

        try:
            response = self._client().get(f"{self.base_url}/{yahoo_symbol}", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise MarketDataFetchError(
                f"yahoo fetch failed for {ticker_upper}: {exc}"
            ) from exc
        except ValueError as exc:
            raise MarketDataFetchError(
                f"yahoo returned invalid JSON for {ticker_upper}"
            ) from exc

        return self._parse_payload(ticker_upper, timeframe, payload)

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        return httpx.Client(timeout=self.timeout_seconds)

    def _query_params(
        self,
        *,
        timeframe: str,
        interval: str,
        start: date | datetime | None,
        end: date | datetime | None,
    ) -> dict[str, str | int]:
        params: dict[str, str | int] = {
            "interval": interval,
            "events": "history",
            "includeAdjustedClose": "true",
        }

        start_dt = _as_utc_datetime(start)
        end_dt = _as_utc_datetime(end)
        if start_dt is None:
            params["range"] = DEFAULT_RANGE_BY_TIMEFRAME[timeframe]
        else:
            params["period1"] = int(start_dt.timestamp())
            params["period2"] = int((end_dt or datetime.now(tz=UTC)).timestamp())
        return params

    def _parse_payload(
        self,
        ticker: str,
        timeframe: str,
        payload: Mapping[str, Any],
    ) -> list[MarketBarDTO]:
        chart = payload.get("chart")
        if not isinstance(chart, Mapping):
            raise MarketDataFetchError(f"yahoo response missing chart for {ticker}")

        error = chart.get("error")
        if error:
            raise MarketDataFetchError(f"yahoo error for {ticker}: {error}")

        results = chart.get("result")
        if not isinstance(results, list) or not results:
            raise MarketDataFetchError(f"yahoo response has no result for {ticker}")

        result = results[0]
        if not isinstance(result, Mapping):
            raise MarketDataFetchError(f"yahoo result has invalid shape for {ticker}")

        timestamps = result.get("timestamp")
        indicators = result.get("indicators")
        if not isinstance(timestamps, list) or not isinstance(indicators, Mapping):
            raise MarketDataFetchError(f"yahoo response has no bars for {ticker}")

        quote_rows = indicators.get("quote")
        if not isinstance(quote_rows, list) or not quote_rows:
            raise MarketDataFetchError(f"yahoo response has no quote rows for {ticker}")
        quote = quote_rows[0]
        if not isinstance(quote, Mapping):
            raise MarketDataFetchError(f"yahoo quote has invalid shape for {ticker}")

        adjclose_values = _first_indicator_values(indicators.get("adjclose"), "adjclose")
        bars: list[MarketBarDTO] = []
        for index, raw_ts in enumerate(timestamps):
            close = _decimal_at(quote.get("close"), index)
            if close is None:
                continue
            try:
                bar_time = datetime.fromtimestamp(int(raw_ts), tz=UTC)
            except (TypeError, ValueError, OSError):
                continue

            bars.append(
                MarketBarDTO(
                    ticker=ticker,
                    timeframe=timeframe,
                    bar_time=bar_time,
                    open=_decimal_at(quote.get("open"), index),
                    high=_decimal_at(quote.get("high"), index),
                    low=_decimal_at(quote.get("low"), index),
                    close=close,
                    volume=_decimal_at(quote.get("volume"), index),
                    adj_close=_decimal_at(adjclose_values, index),
                    source=self.source_name,
                )
            )

        if not bars:
            raise MarketDataFetchError(f"yahoo response had no usable close bars for {ticker}")

        bars.sort(key=lambda bar: bar.bar_time)
        return bars


def _as_utc_datetime(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


def _first_indicator_values(value: Any, key: str) -> Any:
    if not isinstance(value, list) or not value:
        return None
    first = value[0]
    if not isinstance(first, Mapping):
        return None
    return first.get(key)


def _decimal_at(values: Any, index: int) -> Decimal | None:
    if not isinstance(values, list) or index >= len(values):
        return None
    raw = values[index]
    if raw is None:
        return None
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
