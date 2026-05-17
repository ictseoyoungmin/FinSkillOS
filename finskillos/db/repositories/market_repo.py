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

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.models import MarketBar


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
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

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

    def count_for(self, ticker: str, timeframe: str) -> int:
        stmt = select(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
        )
        return len(list(self.session.scalars(stmt)))

    def _get(
        self, ticker: str, timeframe: str, bar_time: datetime
    ) -> MarketBar | None:
        stmt = select(MarketBar).where(
            MarketBar.ticker == ticker.upper(),
            MarketBar.timeframe == timeframe,
            MarketBar.bar_time == bar_time,
        )
        return self.session.scalars(stmt).one_or_none()
