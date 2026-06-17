# Phase 19 — v4.2 UI reconstruction

Continues the integer slice sequence. Each slice is one Docker-verified commit on
`main`. **Not a rewrite** — the data / live-empty-error / descriptive-safety layer
is solid and stays. This phase reconstructs only the *presentation*: a shared
density + chart system, then tab-by-tab refinement, removing redundant / dead
panels that grew organically.

Guiding rules (carry into every slice):
- Descriptive-only is unchanged (no buy/sell/execution copy).
- Display decimals per policy: amounts/quantities integer, %/unit-price keep
  decimals (see memory `feedback-display-decimal-policy`).
- Every panel keeps its live / empty / error state; no fixture leaks.
- Visual baselines drift each slice → regenerate where Playwright browsers exist.

## 19.0 — Design foundation (shared primitives)
- **Shared chart standard**: x-axis must render **sparse, point-positioned date
  ticks** (≈6, MM-DD), not every label (today the `LineChart` flexes all N labels →
  illegible "0000111…" on a 270-point series). Reuse the candlestick chart's
  tick-spacing idea. Optional series legend + day-over-day delta affordance.
- **Density tokens**: standard panel padding / gap / font scale; a compact
  `StatRow` primitive so headline stats (TOTAL / LARGEST / CASH / GUARDS) are
  defined once, not duplicated across command-row + snapshot + state-band.
- **Dead-panel audit**: panels that render nothing useful on live data get removed
  or replaced — e.g. Mission **Sector/Theme Exposure = "UNCLASSIFIED 99.9%"**
  (positions carry no sector), the duplicated TOTAL/LARGEST across three regions.

## 19.1 — Mission Control (pilot)
First tab, because it has the new asset chart + pie and the most redundancy.
- Asset chart: **MM-DD x-ticks** (via the shared fix) + a **day-over-day headline**
  ("어제 대비 +X.X% · +₩Y") computed from the daily series.
- Promote the asset chart + allocation to a taller hero row; fold the duplicated
  TOTAL / LARGEST / CASH / GUARDS stats into one StatRow under the goal tracker.
- Drop or replace the all-UNCLASSIFIED Sector/Theme Exposure panels.

## 19.2+ — Per-tab refinement (one or two slices each)
Apply the foundation tab by tab; reuse the shared chart everywhere a series is
shown. Rough order by payoff:
- Control Room (ticker strip + tape + rails density).
- Symbol Lab / Market Kernel (already share the candlestick chart; tighten the
  side rails + state bands).
- Risk / News / Catalyst / Memory / Ops (panel density + empty-state consistency).

## 19.x — Cleanup
Responsive pass, empty-state consistency, visual-baseline regen, doc refresh.

---
## Slice log
- **263** — plan + Mission chart pilot (date axis + day delta).
- **264–266** — Mission: drop dead exposure panels, rebalance grid, fix chart
  default (realized), dedup snapshot Total, tighten chart.
- **267–268** — shared LineChart: respect `height` prop (CSS override fix) +
  integer `valueFormat` (asset tooltip decimals removed).
- **269–270** — Control Room: per-ticker allocation replaces dead exposure;
  shorter tape + drop redundant meta Interpretation (kept InterpretationCards).
- **271–272** — Symbol Lab: drop redundant meta panels (kept SymbolWatchpoints);
  cap side-rail news + collapse folder symbol lists.
- **273** — Market Kernel + Analysis: drop meta panels (MarketKernelInterpretation
  / operational Watchpoints stay).
- **274** — Risk + News: drop meta Integrated Interpretation (Risk verdict was a
  judgment duplicate; News list was data-source boilerplate).
- **275** — Catalyst + Ops: drop the empty Integrated Interpretation (no
  verdict/why/uncertain in payload).
- **276** — Trade Memory: gate empty sector/theme + mistake breakdowns
  (`.length > 0`) so they reappear when populated.
- **277** — regen 9 visual baselines + reconcile the all-tabs structural
  contract (requiredTestIds, Mission/News topline divergence overrides).

## Status — v4.2 core COMPLETE (as of slice 277)
- 19.0 shared chart standard + dead-panel audit: **done**.
- 19.1 Mission pilot: **done**.
- 19.2 per-tab refinement — all 10 tabs covered: **done**.
- 19.x visual-baseline regen + doc refresh: **done** (this slice).

Consciously **not** done (judged unnecessary, not skipped silently):
- **StatRow primitive** — obsolete: the duplication it targeted (TOTAL / LARGEST /
  CASH / GUARDS repeated across command-row + snapshot + state-band) was already
  removed in 265–266, so there is nothing left to consolidate into a primitive.
- **Responsive / mobile pass** — deferred as an optional follow-up; the cockpit is
  a desktop operating surface and no responsive requirement is outstanding. Revisit
  only if a narrow-viewport target is added.
