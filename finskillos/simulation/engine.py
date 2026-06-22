"""Strategy spec + simulation engine (Phase 21).

Pure, deterministic, offline: ``simulate(spec, bars, external)`` replays a
declarative ``StrategySpec`` over historical bars and returns a descriptive
``SimulationResult`` (equity vs benchmark, simulated exposure windows, risk
metrics). Long-only, full-in / flat, single asset for v1. No DB, no orders, no
buy/sell — only simulated *exposure* ON/OFF, framed as research.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from finskillos.simulation.conditions import (
    Condition,
    FeatureRow,
    evaluate,
    referenced_features,
)
from finskillos.simulation.metrics import SimMetrics, build_metrics

SIMULATION_CAPTION = "과거 일봉 데이터로 돌린 백테스트 (미래 성과와 다를 수 있음)."

_SMA_RE = re.compile(r"^sma_(\d+)$")


@dataclass(frozen=True)
class Bar:
    date: str  # ISO date
    close: float


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    name: str
    description: str
    universe: tuple[str, ...]
    entry: Condition
    exit: Condition
    timeframe: str = "1d"


@dataclass(frozen=True)
class EquityPoint:
    date: str
    strategy: float
    benchmark: float
    exposure: bool
    close: float = 0.0
    regime: str | None = None


@dataclass(frozen=True)
class ExposureMarker:
    """A simulated exposure transition for the time-series chart. Descriptive —
    ``kind`` is ENTER (노출 시작) / EXIT (노출 해제), never buy/sell."""

    date: str
    kind: str  # "ENTER" | "EXIT"
    price: float


@dataclass(frozen=True)
class SimulationResult:
    strategy_id: str
    name: str
    ticker: str
    equity_curve: tuple[EquityPoint, ...]
    exposure_segments: tuple[tuple[str, str], ...]
    metrics: SimMetrics
    bar_count: int
    markers: tuple[ExposureMarker, ...] = field(default_factory=tuple)
    # How many bars carried each indicator/regime feature (data-prep coverage).
    coverage: tuple[tuple[str, int], ...] = field(default_factory=tuple)
    safety_caption: str = SIMULATION_CAPTION
    warnings: tuple[str, ...] = field(default_factory=tuple)


# Indicator / regime features the data-prep panel reports coverage for.
_COVERAGE_FEATURES = ("rsi_14", "trend", "regime", "ema_20", "ema_60")


@dataclass(frozen=True)
class WalkForwardWindow:
    """One sequential out-of-sample window of a walk-forward run (each restarts
    fresh at equity 1.0 so periods are compared independently)."""

    index: int
    date_start: str
    date_end: str
    bar_count: int
    total_return: float | None
    sharpe: float | None
    exposure_pct: float
    round_trips: int


def _sma_windows(spec: StrategySpec) -> set[int]:
    names = referenced_features(spec.entry) | referenced_features(spec.exit)
    windows: set[int] = set()
    for name in names:
        m = _SMA_RE.match(name)
        if m:
            windows.add(int(m.group(1)))
    return windows


def build_features(
    bars: Sequence[Bar],
    *,
    sma_windows: set[int],
    external: Sequence[Mapping[str, float | str]] | None = None,
) -> list[FeatureRow]:
    """Per-bar feature rows: close, ret, drawdown_pct, requested sma_N, plus any
    externally-supplied features (rsi_14, trend, regime) aligned by index."""

    closes = [b.close for b in bars]
    rows: list[FeatureRow] = []
    peak = -float("inf")
    for i, close in enumerate(closes):
        peak = max(peak, close)
        ret = (close / closes[i - 1] - 1.0) if i > 0 and closes[i - 1] else 0.0
        row: dict[str, float | str | None] = {
            "close": close,
            "ret": ret,
            "drawdown_pct": (close / peak - 1.0) * 100.0 if peak > 0 else 0.0,
        }
        for window in sma_windows:
            row[f"sma_{window}"] = (
                sum(closes[i - window + 1 : i + 1]) / window
                if i + 1 >= window
                else None
            )
        if external is not None and i < len(external):
            row.update(external[i])
        rows.append(row)
    return rows


def _regime_of(row: FeatureRow) -> str | None:
    value = row.get("regime")
    return value if isinstance(value, str) else None


def simulate(
    spec: StrategySpec,
    bars: Sequence[Bar],
    *,
    external: Sequence[Mapping[str, float | str]] | None = None,
) -> SimulationResult:
    """Replay ``spec`` over ``bars`` (signal at a bar's close sets exposure for the
    next bar — no lookahead)."""

    ticker = spec.universe[0] if spec.universe else "?"
    if len(bars) < 2:
        return SimulationResult(
            strategy_id=spec.strategy_id,
            name=spec.name,
            ticker=ticker,
            equity_curve=(),
            exposure_segments=(),
            metrics=build_metrics(
                equity=[1.0],
                returns=[],
                in_market_days=0,
                total_days=0,
                round_trips=0,
                wins=0,
            ),
            bar_count=len(bars),
            warnings=("Not enough bars to simulate.",),
        )

    feats = build_features(bars, sma_windows=_sma_windows(spec), external=external)
    exposure = False
    equity = bench = 1.0
    curve: list[EquityPoint] = []
    segments: list[tuple[str, str]] = []
    markers: list[ExposureMarker] = []
    strat_returns: list[float] = []
    in_days = round_trips = wins = 0
    seg_start_idx: int | None = None
    seg_entry_equity = 1.0

    for i, bar in enumerate(bars):
        cur = feats[i]
        prev = feats[i - 1] if i > 0 else None
        ret = float(cur.get("ret") or 0.0)
        bench *= 1.0 + ret
        applied = ret if exposure else 0.0
        equity *= 1.0 + applied
        strat_returns.append(applied)
        if exposure:
            in_days += 1
        curve.append(
            EquityPoint(
                date=bar.date,
                strategy=equity,
                benchmark=bench,
                exposure=exposure,
                close=float(bar.close),
                regime=_regime_of(cur),
            )
        )
        # Update exposure for the next bar from this close's signals.
        if not exposure and evaluate(spec.entry, cur, prev):
            exposure = True
            seg_start_idx = i
            seg_entry_equity = equity
            markers.append(ExposureMarker(bar.date, "ENTER", float(bar.close)))
        elif exposure and evaluate(spec.exit, cur, prev):
            exposure = False
            segments.append((bars[seg_start_idx].date, bar.date))
            markers.append(ExposureMarker(bar.date, "EXIT", float(bar.close)))
            round_trips += 1
            wins += 1 if equity > seg_entry_equity else 0
            seg_start_idx = None

    if exposure and seg_start_idx is not None:
        segments.append((bars[seg_start_idx].date, bars[-1].date))
        round_trips += 1
        wins += 1 if equity > seg_entry_equity else 0

    metrics = build_metrics(
        equity=[p.strategy for p in curve],
        returns=strat_returns,
        in_market_days=in_days,
        total_days=len(bars),
        round_trips=round_trips,
        wins=wins,
    )
    coverage = tuple(
        (feat, sum(1 for row in feats if row.get(feat) is not None))
        for feat in _COVERAGE_FEATURES
    )
    return SimulationResult(
        strategy_id=spec.strategy_id,
        name=spec.name,
        ticker=ticker,
        equity_curve=tuple(curve),
        exposure_segments=tuple(segments),
        metrics=metrics,
        bar_count=len(bars),
        markers=tuple(markers),
        coverage=coverage,
    )


def walk_forward(
    spec: StrategySpec,
    bars: list[Bar],
    *,
    windows: int,
    external: list[FeatureRow] | None = None,
) -> list[WalkForwardWindow]:
    """Split the bars into ``windows`` sequential segments and run ``spec`` on each
    independently (fresh equity per window). Returns [] when there aren't enough
    bars to give each window a meaningful length."""

    n = len(bars)
    if windows < 2 or n < windows * 20:
        return []
    size = n // windows
    out: list[WalkForwardWindow] = []
    for i in range(windows):
        lo = i * size
        hi = n if i == windows - 1 else (i + 1) * size
        seg_bars = bars[lo:hi]
        seg_ext = external[lo:hi] if external is not None else None
        res = simulate(spec, seg_bars, external=seg_ext)
        m = res.metrics
        out.append(
            WalkForwardWindow(
                index=i + 1,
                date_start=seg_bars[0].date,
                date_end=seg_bars[-1].date,
                bar_count=len(seg_bars),
                total_return=m.total_return,
                sharpe=m.sharpe,
                exposure_pct=m.exposure_pct,
                round_trips=m.round_trips,
            )
        )
    return out


@dataclass(frozen=True)
class PortfolioPoint:
    date: str
    strategy: float
    benchmark: float
    exposure: float  # fraction of sleeves in-market on this date [0..1]


@dataclass(frozen=True)
class PortfolioResult:
    tickers: tuple[str, ...]
    weight: float
    curve: tuple[PortfolioPoint, ...]
    metrics: SimMetrics
    bar_count: int


def _per_bar_returns(result: SimulationResult):
    """date -> (applied strategy return, raw return, exposed) for one sleeve."""

    applied: dict[str, float] = {}
    raw: dict[str, float] = {}
    exposed: dict[str, bool] = {}
    prev_s = prev_b = 1.0
    for i, p in enumerate(result.equity_curve):
        applied[p.date] = (p.strategy / prev_s - 1.0) if i > 0 and prev_s else 0.0
        raw[p.date] = (p.benchmark / prev_b - 1.0) if i > 0 and prev_b else 0.0
        exposed[p.date] = p.exposure
        prev_s, prev_b = p.strategy, p.benchmark
    return applied, raw, exposed


def synthesize_portfolio(results: list[SimulationResult]) -> PortfolioResult | None:
    """Combine per-ticker backtests into one equal-weight capital curve (strategy
    vs an equal-weight buy-and-hold benchmark). Each sleeve gets 1/N; on a date a
    ticker lacks a bar its sleeve sits in cash. Descriptive synthesis."""

    usable = [r for r in results if r.bar_count > 1]
    if not usable:
        return None
    weight = 1.0 / len(usable)
    maps = [_per_bar_returns(r) for r in usable]
    dates = sorted({d for applied, _, _ in maps for d in applied})
    if len(dates) < 2:
        return None

    port_rets: list[float] = []
    curve: list[PortfolioPoint] = []
    strat = bench = 1.0
    in_market = 0.0
    for d in dates:
        pr = br = ex = 0.0
        for applied, raw, exposed in maps:
            pr += weight * applied.get(d, 0.0)
            br += weight * raw.get(d, 0.0)
            ex += weight * (1.0 if exposed.get(d) else 0.0)
        strat *= 1.0 + pr
        bench *= 1.0 + br
        in_market += ex
        port_rets.append(pr)
        curve.append(PortfolioPoint(date=d, strategy=strat, benchmark=bench, exposure=ex))

    metrics = build_metrics(
        equity=[p.strategy for p in curve],
        returns=port_rets,
        in_market_days=round(in_market),
        total_days=len(dates),
        round_trips=0,
        wins=0,
    )
    return PortfolioResult(
        tickers=tuple(r.ticker for r in usable),
        weight=weight,
        curve=tuple(curve),
        metrics=metrics,
        bar_count=len(dates),
    )
