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
Status: 19.0 + 19.1 in progress (pilot). Later tabs queued.
