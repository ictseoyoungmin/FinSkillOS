"""Phase 21.1 — simulation engine + metrics, on hand-verifiable series.

Pure + offline: the engine takes injected bars, so no DB / network. Exposure uses
ON/OFF semantics (never buy/sell); a safety test asserts the descriptive caption
and result carry no forbidden wording.
"""

from __future__ import annotations

import pytest

from finskillos.guards.base import find_coercive_term
from finskillos.simulation import (
    SIMULATION_CAPTION,
    All,
    Bar,
    Compare,
    Cross,
    StrategySpec,
    simulate,
)
from finskillos.simulation.metrics import max_drawdown, sharpe, total_return


def _bars(closes):
    return [Bar(date=f"2026-01-{i + 1:02d}", close=c) for i, c in enumerate(closes)]


def _spec(entry, exit_):
    return StrategySpec(
        strategy_id="TEST.SPEC",
        name="test",
        description="hand-traced",
        universe=("NVDA",),
        entry=entry,
        exit=exit_,
    )


def test_always_in_matches_benchmark():
    # entry always true, exit never → fully invested from bar-0 close onward.
    spec = _spec(Compare("close", ">", 0.0), Compare("close", "<", 0.0))
    result = simulate(spec, _bars([100, 110, 121, 108.9]))
    last = result.equity_curve[-1]
    assert last.strategy == pytest.approx(last.benchmark, rel=1e-9)
    assert last.benchmark == pytest.approx(1.089, rel=1e-6)
    # Enter at bar-0 close → in for bars 1..3 (1-day entry lag is a v1 artifact).
    assert result.metrics.exposure_pct == pytest.approx(0.75)


def test_momentum_toggle_is_hand_traceable():
    # IN after an up day, OUT after a down day.
    spec = _spec(Compare("ret", ">", 0.0), Compare("ret", "<", 0.0))
    result = simulate(spec, _bars([100, 110, 99, 108.9]))
    last = result.equity_curve[-1]
    assert last.strategy == pytest.approx(0.9, rel=1e-6)
    assert last.benchmark == pytest.approx(1.089, rel=1e-6)
    assert result.metrics.exposure_pct == pytest.approx(0.25)
    assert result.metrics.round_trips == 2
    assert result.metrics.win_rate == pytest.approx(0.0)


def test_markers_track_exposure_transitions_with_prices():
    # IN after an up day, OUT after a down day → ENTER then EXIT markers.
    spec = _spec(Compare("ret", ">", 0.0), Compare("ret", "<", 0.0))
    result = simulate(spec, _bars([100, 110, 99, 108.9]))
    # ENTER (up day) → EXIT (down day) → ENTER again (re-exposed, never exits).
    assert [m.kind for m in result.markers] == ["ENTER", "EXIT", "ENTER"]
    # Each marker carries the close price at its bar (for the price chart).
    assert result.markers[0].price == 110.0
    assert result.markers[1].price == 99.0
    assert result.markers[2].price == 108.9
    # Every equity point carries its close for the time-series chart.
    assert [p.close for p in result.equity_curve] == [100, 110, 99, 108.9]


def test_sma_crossover_runs_and_segments_are_ordered():
    # close crosses above/below its own SMA(2).
    spec = _spec(
        Cross("close", "above", "sma_2"),
        Cross("close", "below", "sma_2"),
    )
    result = simulate(spec, _bars([100, 98, 96, 99, 103, 101, 97, 102]))
    assert result.bar_count == 8
    for start, end in result.exposure_segments:
        assert start <= end


def test_external_features_drive_conditions():
    # Regime + RSI conditions from injected external features.
    bars = _bars([100, 101, 102, 103])
    external = [
        {"regime": "RISK_OFF", "rsi_14": 80.0},
        {"regime": "RECOVERY", "rsi_14": 28.0},
        {"regime": "RECOVERY", "rsi_14": 40.0},
        {"regime": "HEALTHY_BULL", "rsi_14": 75.0},
    ]
    spec = _spec(
        All((Compare("regime", "==", "RECOVERY"), Compare("rsi_14", "<", 30.0))),
        Compare("rsi_14", ">", 70.0),
    )
    result = simulate(spec, bars, external=external)
    # Entry fires at bar 1 (RECOVERY + rsi 28) → in for bars 2,3; exit at bar 3.
    assert result.metrics.exposure_pct == pytest.approx(0.5)
    assert result.equity_curve[1].regime == "RECOVERY"


def test_designed_strategies_fire_on_crafted_inputs():
    """Each Slice-336 design must actually enter AND exit given the conditions it
    targets — proves the specs are well-formed and useful, not just valid."""
    from finskillos.simulation.library import get_strategy

    def _run(sid, closes, external):
        return simulate(get_strategy(sid), _bars(closes), external=external)

    # EMA(20) crosses above EMA(60) → in; crosses below → out.
    ema = _run(
        "EMA_GOLDEN_20_60",
        [100, 101, 103, 102, 100],
        [
            {"ema_20": 98, "ema_60": 100},
            {"ema_20": 101, "ema_60": 100},
            {"ema_20": 103, "ema_60": 101},
            {"ema_20": 100, "ema_60": 102},
            {"ema_20": 99, "ema_60": 102},
        ],
    )
    assert ema.metrics.round_trips == 1

    # close reclaims EMA(60) then loses it.
    rec = _run(
        "EMA60_TREND_RECLAIM",
        [100, 101, 102, 99, 98],
        [{"ema_60": v} for v in (101, 100, 100, 100, 100)],
    )
    assert rec.metrics.round_trips == 1

    # Uptrend + RSI pullback <45 → in; RSI>70 → out.
    pull = _run(
        "TREND_PULLBACK_RSI",
        [100, 99, 98, 99, 100],
        [
            {"trend": "BULLISH", "rsi_14": 50},
            {"trend": "BULLISH", "rsi_14": 40},
            {"trend": "BULLISH", "rsi_14": 50},
            {"trend": "BULLISH", "rsi_14": 75},
            {"trend": "BULLISH", "rsi_14": 60},
        ],
    )
    assert pull.metrics.round_trips == 1

    # Uptrend + drawdown < -8% → in; recovers above -2% → out.
    dip = _run(
        "DIP_BUY_UPTREND",
        [100, 110, 99, 108],
        [{"trend": "BULLISH"} for _ in range(4)],
    )
    assert dip.metrics.round_trips == 1

    # Confirmed breakout: 20 flat bars then a jump above SMA(20) with RSI>50.
    closes = [100.0] * 20 + [110.0, 95.0]
    ext = [{"rsi_14": 60.0}] * 21 + [{"rsi_14": 40.0}]
    brk = _run("BREAKOUT_SMA20_MOMENTUM", closes, ext)
    assert brk.metrics.round_trips == 1


def test_walk_forward_splits_into_independent_windows():
    from finskillos.simulation.engine import walk_forward

    spec = _spec(Compare("ret", ">", 0.0), Compare("ret", "<", 0.0))
    closes = [100 + (i % 7) - 3 for i in range(120)]  # enough bars for 3 windows
    windows = walk_forward(spec, _bars(closes), windows=3)
    assert [w.index for w in windows] == [1, 2, 3]
    assert sum(w.bar_count for w in windows) == 120
    # Each window is a contiguous, ordered slice.
    assert windows[0].date_start <= windows[0].date_end <= windows[1].date_start
    # Too few bars → no windows (don't fabricate tiny segments).
    assert walk_forward(spec, _bars([100, 101, 102]), windows=3) == []


def test_synthesize_portfolio_equal_weights_two_sleeves():
    from finskillos.simulation.engine import synthesize_portfolio

    spec = _spec(Compare("close", ">", 0.0), Compare("close", "<", 0.0))  # always in
    a = simulate(spec, _bars([100, 110, 121]))  # +10%, +10%
    b = simulate(spec, _bars([100, 90, 81]))  # -10%, -10%
    port = synthesize_portfolio([a, b])
    assert port is not None
    assert port.tickers == ("NVDA", "NVDA") and port.weight == 0.5
    # Equal-weight of +10% and -10% each bar ≈ flat, so final ~ start.
    assert port.curve[-1].strategy == pytest.approx(1.0, abs=0.02)
    # Both sleeves always in-market → exposure fraction ~1.0 after entry.
    assert port.curve[-1].exposure == pytest.approx(1.0)
    # Too few usable sleeves → None.
    assert synthesize_portfolio([simulate(spec, _bars([100]))]) is None


def test_metric_formulas_on_known_equity():
    equity = [1.0, 1.1, 0.99, 1.089]
    assert total_return(equity) == pytest.approx(0.089, rel=1e-6)
    assert max_drawdown(equity) == pytest.approx(-0.1, rel=1e-6)
    assert sharpe([0.0, 0.0]) is None  # zero variance → undefined


def test_simulation_output_is_non_coercive():
    # The sim simulates trading, so buy/sell wording is fine — but it must never
    # be coercive (no "지금 사라" / "보장" / guarantees).
    spec = _spec(Compare("ret", ">", 0.0), Compare("ret", "<", 0.0))
    result = simulate(spec, _bars([100, 110, 99, 108.9]))
    assert find_coercive_term(SIMULATION_CAPTION) is None
    assert find_coercive_term(result.safety_caption, result.name) is None
