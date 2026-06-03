"""MarketRepository — upsert + read access for `market_bars`.

The unique key is `(ticker, timeframe, bar_time)` — re-importing the
same bar must update the row, never duplicate it. The repository also
exposes `latest_bar_time` so the service layer can implement the
incremental refresh policy from docs/v2_1/08 §5.5: only request bars
strictly newer than what is already stored.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.models import MarketBar

# Sub-daily timeframes carry several legitimate bars per calendar day, so
# they are never collapsed. Daily-or-coarser timeframes expect at most one
# bar per day; two bars on the same date are a source collision (e.g. a mock
# seed bar at 00:00 UTC alongside a real vendor bar at 04:00 UTC) and must
# render as one point, otherwise the chart sawtooths between the two series.
_INTRADAY_TIMEFRAMES = frozenset(
    {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "4h"}
)


def _source_rank(source: str | None) -> int:
    """Real vendor data outranks the deterministic ``mock`` seed."""
    return 0 if (source or "").lower() == "mock" else 1


def _prefer(candidate: MarketBar, incumbent: MarketBar) -> bool:
    candidate_rank = _source_rank(candidate.source)
    incumbent_rank = _source_rank(incumbent.source)
    if candidate_rank != incumbent_rank:
        return candidate_rank > incumbent_rank
    return candidate.bar_time > incumbent.bar_time


def _dedupe_period_bars(bars: list[MarketBar], timeframe: str) -> list[MarketBar]:
    """Collapse same-period bars for daily-or-coarser timeframes.

    Keeps one bar per calendar day, preferring a real source over ``mock``
    and then the most recent ``bar_time``. Intraday series pass through
    untouched. Tolerates legacy mixed-source rows without a migration."""
    if timeframe in _INTRADAY_TIMEFRAMES:
        return bars
    chosen: dict[object, MarketBar] = {}
    for bar in bars:
        key = bar.bar_time.date()
        incumbent = chosen.get(key)
        if incumbent is None or _prefer(bar, incumbent):
            chosen[key] = bar
    return sorted(chosen.values(), key=lambda bar: bar.bar_time)


class MarketRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_bars(self, bars: Iterable[MarketBarDTO]) -> int:
        """Insert new bars or update existing ones in place. Returns count written."""
        written = 0
        for bar in bars:
            self.upsert_bar(bar)
            written += 1
        return written

    def upsert_bar(self, bar: MarketBarDTO) -> MarketBar:
        existing = self._get(bar.ticker, bar.timeframe, bar.bar_time)
        if existing is None:
            row = MarketBar(
                ticker=bar.ticker.upper(),
                timeframe=bar.timeframe,
                bar_time=bar.bar_time,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                adj_close=bar.adj_close,
                volume=bar.volume,
                source=bar.source,
            )
            self.session.add(row)
            self.session.flush()
            return row

        existing.open = bar.open
        existing.high = bar.high
        existing.low = bar.low
        existing.close = bar.close
        existing.adj_close = bar.adj_close
        existing.volume = bar.volume
        existing.source = bar.source
        self.session.flush()
        return existing

    def list_bars(
        self,
        ticker: str,
        timeframe: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int | None = None,
    ) -> list[MarketBar]:
        stmt = select(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
        )
        if start is not None:
            stmt = stmt.where(MarketBar.bar_time >= start)
        if end is not None:
            stmt = stmt.where(MarketBar.bar_time <= end)
        stmt = stmt.order_by(MarketBar.bar_time)
        bars = _dedupe_period_bars(list(self.session.scalars(stmt)), timeframe)
        if limit is not None:
            bars = bars[:limit]
        return bars

    def latest_bar(self, ticker: str, timeframe: str) -> MarketBar | None:
        stmt = (
            select(MarketBar)
            .where(
                MarketBar.ticker == ticker.upper(),
                MarketBar.timeframe == timeframe,
            )
            .order_by(MarketBar.bar_time.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()

    def latest_bar_time(self, ticker: str, timeframe: str) -> datetime | None:
        latest = self.latest_bar(ticker, timeframe)
        return latest.bar_time if latest is not None else None

    def latest_close(self, ticker: str, timeframe: str) -> Decimal | None:
        latest = self.latest_bar(ticker, timeframe)
        return latest.close if latest is not None else None

    def tickers_with_bars(self, candidates: Iterable[str]) -> set[str]:
        """Return the subset of ``candidates`` that have at least one stored bar.

        Timeframe-agnostic — used for collection coverage hints (which symbols the
        worker has actually fetched). Returns an empty set for an empty input."""
        wanted = {ticker.strip().upper() for ticker in candidates if ticker.strip()}
        if not wanted:
            return set()
        stmt = select(MarketBar.ticker).where(MarketBar.ticker.in_(wanted)).distinct()
        return {ticker for ticker in self.session.scalars(stmt)}

    def count_for(self, ticker: str, timeframe: str) -> int:
        stmt = select(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
        )
        return len(list(self.session.scalars(stmt)))

    def count_bars_by_sources(self, sources: Iterable[str]) -> int:
        wanted = {s for s in sources}
        if not wanted:
            return 0
        stmt = select(func.count(MarketBar.id)).where(MarketBar.source.in_(wanted))
        return int(self.session.scalar(stmt) or 0)

    def tickers_by_sources(self, sources: Iterable[str]) -> list[str]:
        wanted = {s for s in sources}
        if not wanted:
            return []
        stmt = (
            select(MarketBar.ticker)
            .where(MarketBar.source.in_(wanted))
            .distinct()
            .order_by(MarketBar.ticker)
        )
        return list(self.session.scalars(stmt))

    def delete_bars_by_sources(self, sources: Iterable[str]) -> int:
        """Hard-delete every bar whose source is in ``sources``. Returns the count."""
        wanted = {s for s in sources}
        if not wanted:
            return 0
        stmt = delete(MarketBar).where(MarketBar.source.in_(wanted))
        result = self.session.execute(stmt)
        return int(result.rowcount or 0)

    def source_distribution(self) -> dict[str, int]:
        """Stored-bar counts grouped by source (provenance audit, Slice 152)."""
        stmt = select(MarketBar.source, func.count()).group_by(MarketBar.source)
        return {
            (source or "unknown"): int(count)
            for source, count in self.session.execute(stmt)
        }

    def latest_source_by_ticker(
        self, timeframe: str = "1d"
    ) -> dict[str, tuple[str, datetime]]:
        """Per ticker, the source + bar_time of its newest stored bar."""
        stmt = (
            select(MarketBar.ticker, MarketBar.bar_time, MarketBar.source)
            .where(MarketBar.timeframe == timeframe)
            .order_by(MarketBar.ticker, MarketBar.bar_time.desc())
        )
        latest: dict[str, tuple[str, datetime]] = {}
        for ticker, bar_time, source in self.session.execute(stmt):
            if ticker not in latest:
                latest[ticker] = (source or "unknown", bar_time)
        return latest

    def delete_for(self, ticker: str, timeframe: str) -> int:
        stmt = delete(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
        )
        result = self.session.execute(stmt)
        self.session.flush()
        return int(result.rowcount or 0)

    def _get(
        self, ticker: str, timeframe: str, bar_time: datetime
    ) -> MarketBar | None:
        stmt = select(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
            MarketBar.bar_time == bar_time,
        )
        return self.session.scalars(stmt).one_or_none()
