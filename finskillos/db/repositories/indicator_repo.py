"""IndicatorRepository — upsert + read access for `indicator_snapshots`."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.data_sources.dto import IndicatorSnapshotDTO
from finskillos.db.models import IndicatorSnapshot


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

    def _get(
        self, ticker: str, timeframe: str, snapshot_time: datetime
    ) -> IndicatorSnapshot | None:
        stmt = select(IndicatorSnapshot).where(
            IndicatorSnapshot.ticker == ticker.upper(),
            IndicatorSnapshot.timeframe == timeframe,
            IndicatorSnapshot.snapshot_time == snapshot_time,
        )
        return self.session.scalars(stmt).one_or_none()
