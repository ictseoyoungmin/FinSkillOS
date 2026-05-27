"""MarketDataService — incremental bar import + read-model access.

Wraps the chosen `BaseMarketDataAdapter` with the repository so the
service layer can:

* `refresh_bars(...)` — for each ticker, look up the last bar already
  stored and ask the adapter only for bars strictly newer than that
  point. New bars are upserted; duplicates are silently merged.
* `get_bars(...)` — read sequence for charts / indicator computation.
* `get_latest_price(...)` — Mission Control hot-path lookup.
* `list_universe()` — surface the configured default symbols.

A per-ticker fetch failure (`MarketDataFetchError`) is logged into the
returned `MarketRefreshReport` and never propagates — FAIL-AC-001.

Slice 04 stays interpretation-first: this service only stores and
returns data. It does not emit trading directives.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources import (
    DEFAULT_TIMEFRAME,
    DEFAULT_US_TICKER_UNIVERSE,
    BaseMarketDataAdapter,
    MarketDataFetchError,
    MockMarketDataAdapter,
)
from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.models import MarketBar
from finskillos.db.repositories import MarketRepository

log = logging.getLogger(__name__)

UTC = timezone.utc


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes even for tz-aware columns; normalize."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


@dataclass(frozen=True)
class TickerRefreshResult:
    ticker: str
    timeframe: str
    bars_written: int
    last_bar_time: datetime | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class MarketRefreshReport:
    """Aggregate result of a `refresh_bars` pass.

    Used by Data Health to decide whether to flag stale / partial state
    in the Control Room (see docs/v2_1/08 §13.1). Carries per-ticker
    detail so callers can show exactly which symbols are missing.
    """

    timeframe: str
    results: tuple[TickerRefreshResult, ...] = field(default_factory=tuple)

    @property
    def succeeded(self) -> tuple[TickerRefreshResult, ...]:
        return tuple(r for r in self.results if r.ok)

    @property
    def failed(self) -> tuple[TickerRefreshResult, ...]:
        return tuple(r for r in self.results if not r.ok)

    @property
    def total_bars_written(self) -> int:
        return sum(r.bars_written for r in self.results)


class MarketDataService:
    def __init__(
        self,
        session: Session,
        adapter: BaseMarketDataAdapter | None = None,
        *,
        universe: Sequence[str] | None = None,
    ) -> None:
        self.session = session
        self.adapter = adapter or MockMarketDataAdapter()
        self.market_repo = MarketRepository(session)
        self.universe = tuple(t.upper() for t in (universe or DEFAULT_US_TICKER_UNIVERSE))

    def list_universe(self) -> tuple[str, ...]:
        return self.universe

    def refresh_bars(
        self,
        tickers: Iterable[str] | None = None,
        timeframe: str = DEFAULT_TIMEFRAME,
        *,
        end: datetime | None = None,
        force_full: bool = False,
    ) -> MarketRefreshReport:
        target_tickers = tuple(
            t.upper() for t in (tickers if tickers is not None else self.universe)
        )

        results: list[TickerRefreshResult] = []
        for ticker in target_tickers:
            results.append(
                self._refresh_one(ticker, timeframe, end=end, force_full=force_full)
            )
        return MarketRefreshReport(timeframe=timeframe, results=tuple(results))

    def _refresh_one(
        self,
        ticker: str,
        timeframe: str,
        *,
        end: datetime | None,
        force_full: bool,
    ) -> TickerRefreshResult:
        latest_row = self.market_repo.latest_bar(ticker, timeframe)
        latest_existing = _as_utc(latest_row.bar_time if latest_row else None)
        adapter_source = getattr(self.adapter, "source_name", None)
        if force_full or (
            latest_row is not None and adapter_source and latest_row.source != adapter_source
        ):
            latest_existing = None
        try:
            new_bars = self.adapter.fetch_bars(
                ticker,
                timeframe=timeframe,
                start=latest_existing,
                end=end,
            )
        except MarketDataFetchError as exc:
            log.warning(
                "market data fetch failed for %s %s: %s", ticker, timeframe, exc
            )
            return TickerRefreshResult(
                ticker=ticker,
                timeframe=timeframe,
                bars_written=0,
                last_bar_time=latest_existing,
                error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 — adapters may raise anything
            log.exception(
                "unexpected adapter failure for %s %s", ticker, timeframe
            )
            return TickerRefreshResult(
                ticker=ticker,
                timeframe=timeframe,
                bars_written=0,
                last_bar_time=latest_existing,
                error=f"{type(exc).__name__}: {exc}",
            )

        # Drop any bar already at/before the latest stored one so we
        # genuinely only persist new history (docs/v2_1/08 §5.5).
        if latest_existing is not None:
            new_bars = [
                b for b in new_bars if _as_utc(b.bar_time) > latest_existing
            ]

        if not new_bars:
            return TickerRefreshResult(
                ticker=ticker,
                timeframe=timeframe,
                bars_written=0,
                last_bar_time=latest_existing,
            )

        if force_full:
            self.market_repo.delete_for(ticker, timeframe)
        written = self.market_repo.upsert_bars(new_bars)
        last_time = max(b.bar_time for b in new_bars)
        return TickerRefreshResult(
            ticker=ticker,
            timeframe=timeframe,
            bars_written=written,
            last_bar_time=last_time,
        )

    def import_bars(self, bars: Iterable[MarketBarDTO]) -> int:
        """Bypass the adapter and upsert pre-built bars (CSV imports, tests)."""
        return self.market_repo.upsert_bars(bars)

    def get_bars(
        self,
        ticker: str,
        timeframe: str = DEFAULT_TIMEFRAME,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[MarketBar]:
        return self.market_repo.list_bars(
            ticker, timeframe, start=start, end=end, limit=limit
        )

    def get_latest_price(
        self, ticker: str, timeframe: str = DEFAULT_TIMEFRAME
    ) -> Decimal | None:
        return self.market_repo.latest_close(ticker, timeframe)
