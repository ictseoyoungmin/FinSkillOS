"""SignalService — turn stored bars into indicator snapshots.

The service reads `market_bars` for a ticker/timeframe, runs the pure
indicator functions from `finskillos.signals.technical`, and upserts
the result into `indicator_snapshots`. Snapshots remain *descriptive*:
they record RSI / EMA / Bollinger / volume z-score / momentum_score /
trend_state for a given point in time. The service explicitly does not
produce buy/sell recommendations.

The default flow only writes the *latest* snapshot per ticker — that
is what Mission Control reads — but `compute_indicators` returns the
full DTO sequence so back-tests and chart pages can backfill history.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.data_sources.dto import IndicatorSnapshotDTO
from finskillos.db.models import IndicatorSnapshot, MarketBar
from finskillos.db.repositories import IndicatorRepository, MarketRepository
from finskillos.signals import technical

log = logging.getLogger(__name__)

MIN_BARS_FOR_INDICATORS = 15  # RSI14 needs >14 bars; below this we skip.


@dataclass(frozen=True)
class IndicatorComputeResult:
    ticker: str
    timeframe: str
    snapshots_written: int
    latest_snapshot_time: datetime | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class SignalService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.market_repo = MarketRepository(session)
        self.indicator_repo = IndicatorRepository(session)

    def compute_indicators(
        self,
        ticker: str,
        timeframe: str = DEFAULT_TIMEFRAME,
        *,
        persist_history: bool = False,
    ) -> IndicatorComputeResult:
        """Compute and upsert indicator snapshots for `ticker`.

        When `persist_history=False` (the default), only the most recent
        snapshot is written — this matches the hot-path Market Kernel
        read model. Pass `persist_history=True` to backfill every bar
        for chart pages / back-tests.
        """

        bars = self.market_repo.list_bars(ticker, timeframe)
        if len(bars) < MIN_BARS_FOR_INDICATORS:
            return IndicatorComputeResult(
                ticker=ticker.upper(),
                timeframe=timeframe,
                snapshots_written=0,
                latest_snapshot_time=None,
                error=(
                    f"insufficient_history:{len(bars)}_bars" if bars else "no_bars"
                ),
            )

        try:
            dtos = self._build_snapshots(ticker, timeframe, bars)
        except Exception as exc:  # noqa: BLE001 — defensive: never crash refresh
            log.exception("indicator computation failed for %s %s", ticker, timeframe)
            return IndicatorComputeResult(
                ticker=ticker.upper(),
                timeframe=timeframe,
                snapshots_written=0,
                latest_snapshot_time=None,
                error=f"{type(exc).__name__}: {exc}",
            )

        to_write = dtos if persist_history else [dtos[-1]]
        self.indicator_repo.upsert_snapshots(to_write)
        return IndicatorComputeResult(
            ticker=ticker.upper(),
            timeframe=timeframe,
            snapshots_written=len(to_write),
            latest_snapshot_time=to_write[-1].snapshot_time,
        )

    def compute_for_universe(
        self,
        tickers: Iterable[str],
        timeframe: str = DEFAULT_TIMEFRAME,
        *,
        persist_history: bool = False,
    ) -> tuple[IndicatorComputeResult, ...]:
        return tuple(
            self.compute_indicators(
                ticker, timeframe, persist_history=persist_history
            )
            for ticker in tickers
        )

    def get_latest_indicators(
        self, tickers: Iterable[str], timeframe: str = DEFAULT_TIMEFRAME
    ) -> dict[str, IndicatorSnapshot | None]:
        return {
            ticker.upper(): self.indicator_repo.latest_for(ticker, timeframe)
            for ticker in tickers
        }

    def _build_snapshots(
        self,
        ticker: str,
        timeframe: str,
        bars: Sequence[MarketBar],
    ) -> list[IndicatorSnapshotDTO]:
        closes: list[Decimal] = [b.close for b in bars]
        volumes: list[Decimal] = [
            b.volume if b.volume is not None else Decimal("0") for b in bars
        ]
        times: list[datetime] = [b.bar_time for b in bars]

        rsi14 = technical.rsi(closes, period=14)
        ema20 = technical.ema(closes, period=20)
        ema60 = technical.ema(closes, period=60)
        ema120 = technical.ema(closes, period=120)
        bands = technical.bollinger(closes, period=20)
        vol_z = technical.volume_zscore(volumes, period=20)
        momentum = technical.momentum_score(closes, period=20)

        dtos: list[IndicatorSnapshotDTO] = []
        for i, ts in enumerate(times):
            bb_mid, bb_upper, bb_lower = bands[i]
            dtos.append(
                IndicatorSnapshotDTO(
                    ticker=ticker.upper(),
                    timeframe=timeframe,
                    snapshot_time=ts,
                    rsi_14=rsi14[i],
                    ema_20=ema20[i],
                    ema_60=ema60[i],
                    ema_120=ema120[i],
                    bb_mid=bb_mid,
                    bb_upper=bb_upper,
                    bb_lower=bb_lower,
                    volume_zscore=vol_z[i],
                    momentum_score=momentum[i],
                    trend_state=technical.trend_state(
                        closes[i], ema20[i], ema60[i], ema120[i]
                    ),
                )
            )
        return dtos
