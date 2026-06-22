"""SimulationService — run a strategy spec over stored DB bars (Phase 21.2).

Reads only historical bars + indicator snapshots + regime history (never live
positions / orders), assembles the per-bar feature series, and runs the pure
engine. Descriptive/research only.
"""

from __future__ import annotations

from dataclasses import replace

from finskillos.db.repositories import (
    IndicatorRepository,
    MarketRegimeRepository,
    MarketRepository,
)
from finskillos.simulation import Bar, SimulationResult, StrategySpec, simulate
from finskillos.simulation.engine import (
    PortfolioResult,
    WalkForwardWindow,
    synthesize_portfolio,
    walk_forward,
)
from finskillos.simulation.library import STRATEGY_LIBRARY, get_strategy

_MIN_BARS = 60


class SimulationService:
    def __init__(self, session) -> None:
        self.session = session
        self.market = MarketRepository(session)
        self.indicators = IndicatorRepository(session)
        self.regimes = MarketRegimeRepository(session)

    def available_tickers(self, timeframe: str = "1d") -> list[str]:
        return self.market.tickers_with_min_bars(timeframe, _MIN_BARS)

    def run(
        self,
        strategy_id: str,
        *,
        ticker: str | None = None,
        timeframe: str = "1d",
    ) -> SimulationResult | None:
        spec = get_strategy(strategy_id)
        if spec is None:
            return None
        return self.run_spec(spec, ticker=ticker, timeframe=timeframe)

    def _bars_and_external(self, ticker: str, timeframe: str):
        rows = self.market.list_bars(ticker, timeframe)
        bars = [
            Bar(date=r.bar_time.date().isoformat(), close=float(r.close))
            for r in rows
            if r.close is not None
        ]
        external = self._external_features(ticker, timeframe, [b.date for b in bars])
        return bars, external

    def run_spec(
        self,
        spec: StrategySpec,
        *,
        ticker: str | None = None,
        timeframe: str = "1d",
    ) -> SimulationResult:
        """Run any StrategySpec (built-in or agent-authored free-form) over the
        chosen ticker's stored bars."""

        chosen = (ticker or spec.universe[0]).upper()
        bars, external = self._bars_and_external(chosen, timeframe)
        return simulate(replace(spec, universe=(chosen,)), bars, external=external)

    def screen_spec(
        self,
        spec: StrategySpec,
        *,
        tickers: list[str] | None = None,
        timeframe: str = "1d",
        limit: int = 40,
    ) -> list[SimulationResult]:
        """Run ``spec`` across many tickers (multi-asset screen). Returns the
        per-ticker results that actually had bars."""

        candidates = tickers or self.available_tickers(timeframe)
        out: list[SimulationResult] = []
        for tk in candidates[:limit]:
            result = self.run_spec(spec, ticker=tk, timeframe=timeframe)
            if result.bar_count > 0:
                out.append(result)
        return out

    def portfolio_spec(
        self,
        spec: StrategySpec,
        *,
        tickers: list[str],
        timeframe: str = "1d",
        limit: int = 12,
    ) -> PortfolioResult | None:
        """Equal-weight portfolio synthesis — run ``spec`` on each ticker and
        combine into one capital curve."""

        results = [
            self.run_spec(spec, ticker=tk, timeframe=timeframe)
            for tk in tickers[:limit]
        ]
        return synthesize_portfolio(results)

    def walk_forward_spec(
        self,
        spec: StrategySpec,
        *,
        ticker: str | None = None,
        timeframe: str = "1d",
        windows: int = 4,
    ) -> list[WalkForwardWindow]:
        """Per-window robustness check — runs ``spec`` over sequential segments."""

        chosen = (ticker or spec.universe[0]).upper()
        bars, external = self._bars_and_external(chosen, timeframe)
        return walk_forward(
            replace(spec, universe=(chosen,)),
            bars,
            windows=windows,
            external=external,
        )

    def _external_features(
        self, ticker: str, timeframe: str, dates: list[str]
    ) -> list[dict[str, float | str]]:
        by_date = {
            r.snapshot_time.date().isoformat(): r
            for r in self.indicators.list_for(ticker, timeframe)
        }
        regime_marks = sorted(
            (
                (r.snapshot_time.date().isoformat(), r.regime)
                for r in self.regimes.list_recent(limit=10000)
            ),
            key=lambda x: x[0],
        )

        def regime_as_of(day: str) -> str | None:
            current = None
            for mark_day, regime in regime_marks:
                if mark_day <= day:
                    current = regime
                else:
                    break
            return current

        rows: list[dict[str, float | str]] = []
        for day in dates:
            row: dict[str, float | str] = {}
            snap = by_date.get(day)
            if snap is not None:
                if snap.rsi_14 is not None:
                    row["rsi_14"] = float(snap.rsi_14)
                if snap.trend_state:
                    row["trend"] = snap.trend_state
                if snap.ema_20 is not None:
                    row["ema_20"] = float(snap.ema_20)
                if snap.ema_60 is not None:
                    row["ema_60"] = float(snap.ema_60)
            regime = regime_as_of(day)
            if regime is not None:
                row["regime"] = regime
            rows.append(row)
        return rows


def list_strategies() -> list[dict[str, str]]:
    return [
        {"id": s.strategy_id, "name": s.name, "description": s.description}
        for s in STRATEGY_LIBRARY
    ]
