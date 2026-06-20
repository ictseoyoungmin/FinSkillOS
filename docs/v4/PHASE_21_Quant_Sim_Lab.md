# Phase 21 — Quant Simulation Lab ("Strategy Lab")

Continues the integer slice sequence (Phase 20 ended at slice 315). Each slice is
one Docker-verified commit on `main`.

> **What.** A new cockpit tab where the **agent designs descriptive quant
> hypotheses** (declarative strategy specs) and **simulates** them over the DB's
> historical bars, with the result **visualized** (equity curve + regime overlay +
> risk metrics). No real trading, ever.

## 1. Why this fits — and the hard boundary

FinSkillOS is **descriptive-only**: the product never tells the user to buy/sell
their real portfolio. A quant-strategy *backtester* normally violates this (its
output is entry/exit signals + return optimisation). This phase stays inside the
rule by treating the Lab as **research / simulation, explicitly walled off from
the live cockpit**:

- It studies a *hypothesis over history*, not a recommendation for today.
- Simulated transitions use **exposure ON / OFF** vocabulary (in-market / flat),
  never 매수/매도 / buy / sell. The same `find_forbidden_term` scan applies to all
  prose; the simulated events are labelled simulation mechanics.
- Every surface carries: **"시뮬레이션 — 관측됐을 성과이며 매매 권유가 아닙니다."**
- It never reads/writes the user's live positions or places any order. It only
  reads stored historical bars/indicators.

The data supports it: **~24.5k market bars across 41 tickers, span 2016–2026**, +
matching indicator snapshots; the regime engine is deterministic so regime can be
recomputed across the span. Per-series *daily* depth currently varies (e.g. NVDA
1d ≈ 1y / 268 bars) and **deepens as the market-data refresh runs** — the
simulation works at any depth; longer history simply makes the backtest more
meaningful. (Live counts at design time; engine verified on real NVDA/AAPL/QQQ
daily bars.)

## 2. The strategy spec (agent-authored, declarative)

Reuses the Skill Layer philosophy — a strategy is a *declarative spec*, not code:

```python
@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    name: str
    description: str
    universe: tuple[str, ...]        # v1: a single ticker
    timeframe: str = "1d"
    entry: Condition                 # exposure ON when true
    exit: Condition                  # exposure OFF when true
    # v1 sizing: long-only, full-in / flat; one asset.

# Condition = a composable predicate over per-bar features
#   feature(RSI_14 | TREND | CLOSE | SMA_20 | DRAWDOWN | REGIME | ...)
#   comparator (<, <=, >, >=, ==, crosses_above, crosses_below)
#   + AND / OR composition.
```

Features come from the **same sources the skills use** (indicator snapshots,
regime classification), so a hypothesis is expressed in the cockpit's own
vocabulary ("회복 국면 + RSI 과매도 반등"). The agent composes a `StrategySpec`
from natural language (Phase 21.4).

## 3. The simulation engine (`finskillos/simulation/`)

Pure + deterministic + offline (no DB inside — the service feeds bars/indicators):

```
simulate(spec, bars, features) -> SimulationResult
```
- Replays bar-by-bar in order. On each bar, evaluate `entry`/`exit` over that
  bar's features → maintain `exposure` (IN/OUT). Returns accrue on the held asset
  on IN days. Long-only, full-in/flat for v1; transaction-cost stub.
- `SimulationResult`:
  - `equity_curve`: (date, strategy_equity, benchmark_equity) — benchmark =
    buy-and-hold of the same asset.
  - `exposure_segments`: simulated IN windows (for shading + markers).
  - `metrics`: total return, CAGR, annualised vol, **Sharpe / Sortino / Calmar /
    max drawdown** (the absorbed legacy METRIC rulebook — `docs/v4/SKILL_RULEBOOK.md`
    §1, now implemented), exposure %, number of round-trips, win rate.
  - `regime_overlay`: regime per date (recomputed) for the timeline shading.

## 4. Phasing

- **21.0** — this design.
- **21.1** — engine core: `StrategySpec` / `Condition` + `simulate()` + the
  METRIC functions, with a deterministic test on real-shaped bar series (the
  prototype that proves the maths). Pure, offline.
- **21.2** — `SimulationService`: read bars/indicators from the DB
  (`MarketRepository.list_bars` / `IndicatorRepository.list_for`), run a spec,
  build the read model; `/api/quant-lab` route + schema (descriptive, safety
  caption). A couple of built-in example specs so the tab renders before the agent.
- **21.3** — frontend **Quant Lab** tab: equity curve vs benchmark (shared
  LineChart), regime-shaded timeline, exposure markers, metrics panel, the spec
  shown as evidence. Visual baseline + the all-tabs structural contract entry.
- **21.4** — agent designs the spec: NL → `StrategySpec` (a `{"strategy": …}`
  block like the protocol/need blocks) → run → the tab visualises. Edit/iterate.
- **21.x** — multi-asset / portfolio sims, walk-forward windows, saved specs.

## 5. Guardrails carried into every slice
- Descriptive-only: exposure ON/OFF vocabulary, never buy/sell; every surface
  carries the simulation/not-advice caption; `find_forbidden_term` on all prose.
- Engine is pure + deterministic + offline-testable (no DB inside; injected bars).
- Reads only stored historical bars/indicators; never touches live positions/orders.
- Display-decimal policy unchanged (%/ratios keep decimals, amounts integer).

---
Status: 21.0 design + 21.1 engine prototype built alongside this doc. 21.2+ queued.
