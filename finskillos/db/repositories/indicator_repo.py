"""IndicatorRepository — upsert + read access for `indicator_snapshots`."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO
from finskillos.db.models import IndicatorSnapshot, MarketBar


class IndicatorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_snapshots(self, dtos: Iterable[IndicatorSnapshotDTO]) -> int:
        count = 0
        for dto in dtos:
            self.upsert_snapshot(dto)
            count += 1
        return count

    def upsert_snapshot(self, dto: IndicatorSnapshotDTO) -> IndicatorSnapshot:
        existing = self._get(dto.ticker, dto.timeframe, dto.snapshot_time)
        if existing is None:
            row = IndicatorSnapshot(
                ticker=dto.ticker.upper(),
                timeframe=dto.timeframe,
                snapshot_time=dto.snapshot_time,
                rsi_14=dto.rsi_14,
                ema_20=dto.ema_20,
                ema_60=dto.ema_60,
                ema_120=dto.ema_120,
                bb_mid=dto.bb_mid,
                bb_upper=dto.bb_upper,
                bb_lower=dto.bb_lower,
                volume_zscore=dto.volume_zscore,
                momentum_score=dto.momentum_score,
                trend_state=dto.trend_state,
                source=dto.source,
            )
            self.session.add(row)
            self.session.flush()
            return row

        existing.rsi_14 = dto.rsi_14
        existing.ema_20 = dto.ema_20
        existing.ema_60 = dto.ema_60
        existing.ema_120 = dto.ema_120
        existing.bb_mid = dto.bb_mid
        existing.bb_upper = dto.bb_upper
        existing.bb_lower = dto.bb_lower
        existing.volume_zscore = dto.volume_zscore
        existing.momentum_score = dto.momentum_score
        existing.trend_state = dto.trend_state
        existing.source = dto.source
        self.session.flush()
        return existing

    def latest_for(
        self, ticker: str, timeframe: str
    ) -> IndicatorSnapshot | None:
        stmt = (
            select(IndicatorSnapshot)
            .where(
                IndicatorSnapshot.ticker == ticker.upper(),
                IndicatorSnapshot.timeframe == timeframe,
            )
            .order_by(IndicatorSnapshot.snapshot_time.desc())
            .limit(1)
        )
        return self.session.scalars(stmt).one_or_none()

    def list_for(
        self,
        ticker: str,
        timeframe: str,
        *,
        limit: int | None = None,
    ) -> list[IndicatorSnapshot]:
        stmt = (
            select(IndicatorSnapshot)
            .where(
                IndicatorSnapshot.ticker == ticker.upper(),
                IndicatorSnapshot.timeframe == timeframe,
            )
            .order_by(IndicatorSnapshot.snapshot_time)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt))

    def _orphan_filter(self):
        """Snapshots with no backing market bar at the same key (Slice 102/153)."""
        backing = (
            select(MarketBar.id)
            .where(
                MarketBar.ticker == IndicatorSnapshot.ticker,
                MarketBar.timeframe == IndicatorSnapshot.timeframe,
                MarketBar.bar_time == IndicatorSnapshot.snapshot_time,
            )
            .exists()
        )
        return ~backing

    def count_total(self) -> int:
        return int(self.session.scalar(select(func.count(IndicatorSnapshot.id))) or 0)

    def count_orphan_snapshots(self) -> int:
        """Indicator snapshots with no backing market bar (an invariant violation)."""
        stmt = select(func.count(IndicatorSnapshot.id)).where(self._orphan_filter())
        return int(self.session.scalar(stmt) or 0)

    def list_orphan_snapshots(
        self, limit: int = 15
    ) -> list[tuple[str, str, datetime]]:
        stmt = (
            select(
                IndicatorSnapshot.ticker,
                IndicatorSnapshot.timeframe,
                IndicatorSnapshot.snapshot_time,
            )
            .where(self._orphan_filter())
            .order_by(IndicatorSnapshot.snapshot_time.desc())
            .limit(limit)
        )
        return [tuple(row) for row in self.session.execute(stmt)]

    def delete_orphan_snapshots(self) -> int:
        """Hard-delete indicator snapshots with no backing market bar. Returns count.

        Uses a PK subquery + IN delete so it works on both SQLite and Postgres
        (neither supports a correlated EXISTS in a DELETE the same way)."""
        from sqlalchemy import delete

        orphan_ids = select(IndicatorSnapshot.id).where(self._orphan_filter())
        ids = [row for row in self.session.scalars(orphan_ids)]
        if not ids:
            return 0
        result = self.session.execute(
            delete(IndicatorSnapshot).where(IndicatorSnapshot.id.in_(ids))
        )
        return int(result.rowcount or 0)

    def _get(
        self, ticker: str, timeframe: str, snapshot_time: datetime
    ) -> IndicatorSnapshot | None:
        stmt = select(IndicatorSnapshot).where(
            IndicatorSnapshot.ticker == ticker.upper(),
            IndicatorSnapshot.timeframe == timeframe,
            IndicatorSnapshot.snapshot_time == snapshot_time,
        )
        return self.session.scalars(stmt).one_or_none()
