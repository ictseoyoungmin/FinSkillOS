"""Market data adapter abstraction + offline-friendly implementations.

docs/v2_1/08 §2.2 mandates provider-agnostic adapters. Real providers
(yfinance, Alpha Vantage, Polygon) plug in by subclassing
`BaseMarketDataAdapter` and emitting `MarketBarDTO` instances.

Two adapters are shipped with Slice 04 so the rest of the system never
hits an external API in tests or in offline development:

* `MockMarketDataAdapter` — deterministic sinusoidal+drift generator
  seeded per ticker. Same inputs always produce the same bars, which
  keeps signal-calculation tests reproducible without any disk I/O.
* `CsvMarketDataAdapter` — loads bars from a CSV fixture
  (see ``tests/fixtures/market_bars/sample_daily_bars.csv``). Useful
  for hand-authored scenarios in DATA-AC-001 / DATA-AC-002.

Adapter failures must never bring down the application. Callers should
treat `MarketDataFetchError` as a soft failure: log it and move on to
the next ticker (FAIL-AC-001 from docs/v2_1/09).
"""

from __future__ import annotations

import csv
import math
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from finskillos.data_sources.dto import MarketBarDTO

UTC = timezone.utc


class MarketDataFetchError(RuntimeError):
    """Raised by an adapter when a per-ticker fetch fails.

    Services must catch this and continue with the next ticker so a
    single bad symbol does not crash the refresh pass.
    """


class BaseMarketDataAdapter(ABC):
    """Provider-agnostic market-data adapter.

    Implementations are responsible for emitting bars in chronological
    order so the service layer can rely on the tail of the list being
    the latest bar.
    """

    source_name: str = "base"

    @abstractmethod
    def fetch_bars(
        self,
        ticker: str,
        *,
        timeframe: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[MarketBarDTO]:
        """Return chronological bars for `ticker` in `timeframe`."""


def _coerce_dt(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime(value.year, value.month, value.day, tzinfo=UTC)


def _bar_seconds(timeframe: str) -> int:
    table = {
        "1h": 3600,
        "1d": 86400,
        "1wk": 604800,
        "1mo": 2592000,
    }
    if timeframe not in table:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return table[timeframe]


def _ticker_seed(ticker: str) -> int:
    """Stable per-ticker integer seed (no Python hash randomization)."""
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(ticker.upper()))


class MockMarketDataAdapter(BaseMarketDataAdapter):
    """Deterministic offline market-data adapter.

    Produces a sinusoidal close path with a small linear drift so the
    bars look plausible (visible swings, trending) while remaining
    perfectly reproducible. The same `(ticker, timeframe, start, end)`
    always yields the same bars — no global state, no time-of-day
    dependence — so it is safe to share between tests.

    `failing_tickers` lets tests assert FAIL-AC-001: any ticker in the
    set raises `MarketDataFetchError` instead of returning bars.
    """

    source_name = "mock"

    def __init__(
        self,
        *,
        default_start: date = date(2026, 1, 5),
        default_bars: int = 180,
        failing_tickers: set[str] | None = None,
    ) -> None:
        self.default_start = default_start
        self.default_bars = default_bars
        self.failing_tickers = {t.upper() for t in (failing_tickers or set())}

    def fetch_bars(
        self,
        ticker: str,
        *,
        timeframe: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[MarketBarDTO]:
        ticker_upper = ticker.upper()
        if ticker_upper in self.failing_tickers:
            raise MarketDataFetchError(
                f"mock adapter configured to fail for {ticker_upper}"
            )

        seconds = _bar_seconds(timeframe)
        start_dt = _coerce_dt(start) or datetime(
            self.default_start.year,
            self.default_start.month,
            self.default_start.day,
            tzinfo=UTC,
        )
        end_dt = _coerce_dt(end) or start_dt + timedelta(
            seconds=seconds * (self.default_bars - 1)
        )

        if end_dt < start_dt:
            return []

        seed = _ticker_seed(ticker_upper)
        # Base price between roughly 50 and 550 — same scale as real US equities.
        base_price = 50.0 + (seed % 500)
        amplitude = max(2.0, base_price * 0.05)
        drift = ((seed % 7) - 3) * 0.05  # range [-0.15, +0.15] per bar

        bars: list[MarketBarDTO] = []
        cursor = start_dt
        step = 0
        while cursor <= end_dt:
            angle = (seed + step) * 0.13
            wave = math.sin(angle) * amplitude
            trend = drift * step
            close = base_price + wave + trend
            open_px = base_price + math.sin(angle - 0.05) * amplitude + trend
            high = max(open_px, close) + amplitude * 0.25
            low = min(open_px, close) - amplitude * 0.25
            volume = 1_000_000 + ((seed + step) % 1000) * 5_000

            bars.append(
                MarketBarDTO(
                    ticker=ticker_upper,
                    timeframe=timeframe,
                    bar_time=cursor,
                    open=Decimal(f"{open_px:.6f}"),
                    high=Decimal(f"{high:.6f}"),
                    low=Decimal(f"{low:.6f}"),
                    close=Decimal(f"{close:.6f}"),
                    volume=Decimal(volume),
                    source=self.source_name,
                )
            )
            cursor = cursor + timedelta(seconds=seconds)
            step += 1

        return bars


class CsvMarketDataAdapter(BaseMarketDataAdapter):
    """Read bars from a CSV fixture grouped by ticker.

    Expected columns: ``ticker,timeframe,bar_time,open,high,low,close,volume``.
    `bar_time` is parsed via `datetime.fromisoformat`. Missing tickers
    raise `MarketDataFetchError` so callers can test fallback paths.
    """

    source_name = "csv"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._cache: dict[str, list[MarketBarDTO]] | None = None

    def _load(self) -> dict[str, list[MarketBarDTO]]:
        if self._cache is not None:
            return self._cache
        if not self.path.exists():
            raise MarketDataFetchError(f"market-data CSV not found: {self.path}")

        grouped: dict[str, list[MarketBarDTO]] = {}
        with self.path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for raw in reader:
                ticker = (raw.get("ticker") or "").strip().upper()
                if not ticker:
                    continue
                bar_time_raw = (raw.get("bar_time") or "").strip()
                bar_time = datetime.fromisoformat(bar_time_raw)
                if bar_time.tzinfo is None:
                    bar_time = bar_time.replace(tzinfo=UTC)
                grouped.setdefault(ticker, []).append(
                    MarketBarDTO(
                        ticker=ticker,
                        timeframe=(raw.get("timeframe") or "1d").strip(),
                        bar_time=bar_time,
                        open=_dec(raw.get("open")),
                        high=_dec(raw.get("high")),
                        low=_dec(raw.get("low")),
                        close=_dec(raw.get("close")) or Decimal("0"),
                        volume=_dec(raw.get("volume")),
                        source=self.source_name,
                    )
                )
        for bars in grouped.values():
            bars.sort(key=lambda b: b.bar_time)
        self._cache = grouped
        return grouped

    def fetch_bars(
        self,
        ticker: str,
        *,
        timeframe: str = "1d",
        start: date | datetime | None = None,
        end: date | datetime | None = None,
    ) -> list[MarketBarDTO]:
        cache = self._load()
        ticker_upper = ticker.upper()
        if ticker_upper not in cache:
            raise MarketDataFetchError(
                f"csv adapter has no data for {ticker_upper}"
            )

        start_dt = _coerce_dt(start)
        end_dt = _coerce_dt(end)
        result: list[MarketBarDTO] = []
        for bar in cache[ticker_upper]:
            if bar.timeframe != timeframe:
                continue
            if start_dt is not None and bar.bar_time < start_dt:
                continue
            if end_dt is not None and bar.bar_time > end_dt:
                continue
            result.append(bar)
        return result


def _dec(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned == "":
        return None
    return Decimal(cleaned)
