"""RegimeService — assemble a RegimeInput from stored snapshots.

Pulls the indicators we already persist in Slice 04 (`indicator_snapshots`
for SPY / QQQ / SMH / DXY / US10Y) plus the latest VIX bar
(`market_bars.close`), builds the canonical `RegimeInput`, and hands it
to the pure rule engine.

Missing data is *tolerated*: tickers without any history simply become
`None` fields, the engine returns `UNKNOWN` (or a low-confidence
classification), and the service never raises. This matches
docs/v2_1/09 FAIL-AC-004 (insufficient indicator history must not crash
the engine) and the slice-05 acceptance criteria.

The service can also persist the result via `MarketRegimeRepository`
when `persist=True` so Mission Control can read the latest classification
without recomputing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.data_sources import DEFAULT_TIMEFRAME
from finskillos.db.models import IndicatorSnapshot, MarketRegime
from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.regime import RegimeInput, RegimeOutput, classify_regime

log = logging.getLogger(__name__)

UTC = timezone.utc

DEFAULT_INDEX_TICKERS: tuple[str, ...] = ("SPY", "QQQ", "SMH")
DEFAULT_MACRO_TICKERS: tuple[str, ...] = ("DXY", "US10Y")
DEFAULT_VIX_TICKER: str = "VIX"


class RegimeService:
    def __init__(
        self,
        session: Session,
        *,
        timeframe: str = DEFAULT_TIMEFRAME,
    ) -> None:
        self.session = session
        self.timeframe = timeframe
        self.indicator_repo = IndicatorRepository(session)
        self.market_repo = MarketRepository(session)
        self.regime_repo = MarketRegimeRepository(session)

    # ------------------------------------------------------------------
    # Input assembly
    # ------------------------------------------------------------------

    def build_input(self) -> RegimeInput:
        spy = self._latest_indicator("SPY")
        qqq = self._latest_indicator("QQQ")
        smh = self._latest_indicator("SMH")
        dxy = self._latest_indicator("DXY")
        us10y = self._latest_indicator("US10Y")

        return RegimeInput(
            spy_trend_state=_trend(spy),
            qqq_trend_state=_trend(qqq),
            smh_trend_state=_trend(smh),
            spy_rsi_14=_rsi(spy),
            qqq_rsi_14=_rsi(qqq),
            smh_rsi_14=_rsi(smh),
            vix_close=self._latest_vix_close(),
            dxy_trend_state=_trend(dxy),
            us10y_trend_state=_trend(us10y),
            momentum_score=_momentum(qqq),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_today_regime(
        self,
        *,
        snapshot_time: datetime | None = None,
        persist: bool = True,
    ) -> RegimeOutput:
        """Compute the current regime and optionally persist the snapshot."""

        inputs = self.build_input()
        output = classify_regime(inputs)
        if persist:
            self.regime_repo.record(
                snapshot_time=_resolve_snapshot_time(snapshot_time),
                output=output,
            )
        return output

    def get_latest_regime(self) -> MarketRegime | None:
        return self.regime_repo.latest()

    def get_regime_history(self, *, limit: int = 30) -> list[MarketRegime]:
        return self.regime_repo.list_recent(limit=limit)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _latest_indicator(self, ticker: str) -> IndicatorSnapshot | None:
        return self.indicator_repo.latest_for(ticker, self.timeframe)

    def _latest_vix_close(self) -> Decimal | None:
        # Prefer the indicator snapshot's bb_mid is meaningless for VIX —
        # the canonical "where is VIX right now?" reading is the latest
        # bar close. Slice 04's MarketRepository already exposes that.
        return self.market_repo.latest_close(DEFAULT_VIX_TICKER, self.timeframe)


def _trend(snapshot: IndicatorSnapshot | None) -> str | None:
    return snapshot.trend_state if snapshot is not None else None


def _rsi(snapshot: IndicatorSnapshot | None) -> Decimal | None:
    return snapshot.rsi_14 if snapshot is not None else None


def _momentum(snapshot: IndicatorSnapshot | None) -> Decimal | None:
    return snapshot.momentum_score if snapshot is not None else None


def _resolve_snapshot_time(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(tz=UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
