"""Quant Lab fixture + shared result→response converter (Phase 21.2).

The converter maps a pure ``SimulationResult`` onto the camelCase read model and
is reused by the live route. The fixture itself runs the engine on a deterministic
synthetic bar series (no DB, no network), so the tab renders an honest, hand-shaped
backtest before the live DB is reached.
"""

from __future__ import annotations

import math
from datetime import timezone

from api.schemas.common import JudgmentHeader, SystemStatus
from api.schemas.quant_lab import (
    QuantLabCoverage,
    QuantLabDataState,
    QuantLabEquityPoint,
    QuantLabFeatureCoverage,
    QuantLabMarker,
    QuantLabMetrics,
    QuantLabResponse,
    QuantLabSegment,
    QuantLabStrategyOption,
    QuantLabStrategySummary,
)
from finskillos.services.simulation_service import list_strategies
from finskillos.simulation import SIMULATION_CAPTION, Bar, SimulationResult, simulate
from finskillos.simulation.library import condition_text, get_strategy

UTC = timezone.utc
FIXTURE_TIMESTAMP = "2026-06-20T00:00:00+00:00"
_FIXTURE_TICKERS = ["NVDA", "AAPL", "QQQ", "TSLA", "MSFT"]


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def build_quant_lab_response(
    result: SimulationResult,
    *,
    strategy_id: str,
    available_tickers: list[str],
    source: str,
    generated_at: str,
    regime_covered: bool,
    db_state: str = "LIVE",
    spec=None,
) -> QuantLabResponse:
    # ``spec`` is the actual StrategySpec (needed for agent-authored CUSTOM specs
    # that aren't in the library); fall back to the built-in lookup by id.
    spec = spec or get_strategy(strategy_id)
    entry_text = condition_text(spec.entry) if spec is not None else ""
    exit_text = condition_text(spec.exit) if spec is not None else ""

    m = result.metrics
    metrics = QuantLabMetrics(
        total_return=m.total_return,
        cagr=m.cagr,
        annual_volatility=m.annual_volatility,
        sharpe=m.sharpe,
        sortino=m.sortino,
        max_drawdown=m.max_drawdown,
        calmar=m.calmar,
        exposure_pct=m.exposure_pct,
        round_trips=m.round_trips,
        win_rate=m.win_rate,
    )
    curve = [
        QuantLabEquityPoint(
            date=p.date,
            strategy=p.strategy,
            benchmark=p.benchmark,
            exposure=bool(p.exposure),
            close=p.close,
            regime=p.regime,
        )
        for p in result.equity_curve
    ]
    segments = [
        QuantLabSegment(start=start, end=end)
        for start, end in result.exposure_segments
    ]
    markers = [
        QuantLabMarker(date=mk.date, kind=mk.kind, price=mk.price)
        for mk in result.markers
    ]
    bc = result.bar_count or 1
    coverage = QuantLabCoverage(
        date_start=result.equity_curve[0].date if result.equity_curve else "",
        date_end=result.equity_curve[-1].date if result.equity_curve else "",
        bar_count=result.bar_count,
        features=[
            QuantLabFeatureCoverage(name=name, bars=bars, pct=bars / bc)
            for name, bars in result.coverage
        ],
    )

    summary = (
        f"보유 비중 {_pct(m.exposure_pct)} · 누적 {_pct(m.total_return)} "
        f"(단순 보유 대비). {result.bar_count}개 일봉 바 백테스트."
    )
    judgment = JudgmentHeader(
        eyebrow="QUANT LAB · 시뮬레이션",
        title=result.name,
        accent=result.ticker,
        summary=summary,
        confidence=0,
    )

    return QuantLabResponse(
        generated_at=generated_at,
        system_status=SystemStatus(db=db_state, guard_count=0),
        judgment=judgment,
        strategy=QuantLabStrategySummary(
            id=result.strategy_id,
            name=result.name,
            description=spec.description if spec is not None else "",
            ticker=result.ticker,
            entry_text=entry_text,
            exit_text=exit_text,
        ),
        metrics=metrics,
        equity_curve=curve,
        exposure_segments=segments,
        markers=markers,
        available_strategies=[
            QuantLabStrategyOption(**option) for option in list_strategies()
        ],
        available_tickers=available_tickers,
        safety_caption=result.safety_caption,
        data_state=QuantLabDataState(
            source=source,
            ticker=result.ticker,
            bar_count=result.bar_count,
            regime_covered=regime_covered,
            data_note="과거 일봉 바 백테스트.",
        ),
        coverage=coverage,
        warnings=list(result.warnings),
    )


def _synthetic_bars(count: int = 90) -> list[Bar]:
    """A deterministic gently-cyclical uptrend so SMA(50) crossovers actually
    fire — no DB, no randomness."""

    bars: list[Bar] = []
    for i in range(count):
        close = 100.0 * (1.0 + 0.0015 * i) + 8.0 * math.sin(i / 9.0)
        bars.append(Bar(date=f"2025-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", close=round(close, 4)))
    return bars


def quant_lab_fixture(
    strategy_id: str | None = None,
    *,
    ticker: str | None = None,
) -> QuantLabResponse:
    sid = strategy_id or "SMA_50_CROSS"
    spec = get_strategy(sid)
    if spec is None:
        sid = "SMA_50_CROSS"
        spec = get_strategy(sid)
    tk = (ticker or spec.universe[0]).upper()
    from dataclasses import replace

    result = simulate(replace(spec, universe=(tk,)), _synthetic_bars())
    return build_quant_lab_response(
        result,
        strategy_id=sid,
        available_tickers=list(_FIXTURE_TICKERS),
        source="fixture",
        generated_at=FIXTURE_TIMESTAMP,
        regime_covered=False,
        db_state="FIXTURE",
    )


__all__ = [
    "FIXTURE_TIMESTAMP",
    "SIMULATION_CAPTION",
    "build_quant_lab_response",
    "quant_lab_fixture",
]
