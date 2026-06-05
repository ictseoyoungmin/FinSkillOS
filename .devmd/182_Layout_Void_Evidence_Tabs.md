# 182 — Eliminate Layout Void (Evidence Tabs) (v3 Phase 8)

**Status:** Done (iteration 1 — the 4 evidence tabs). Addresses the large
mid-page vertical void the user captured.

## Root cause

The evidence tabs lay out as a multi-column grid (a wide chart/table column + a
side rail) followed by **full-width** Integrated-Interpretation / Watchpoints
sections. The grid row's height = the **tallest** column, so the shorter column
leaves a tall void, and the full-width sections sit far below the fold. The exact
short/tall column differs per tab (a fixed-height chart column is short; a 17-row
table column is tall).

## Fix

Flow the trailing Integrated-Interpretation + Watchpoints panels **into the
shorter column** so it grows to fill the space beside the taller column, removing
the void and pulling the sections above the fold. `SafetyCaption` stays
full-width at the very bottom.

| Tab | Short column (filled) |
|---|---|
| Control Room | center (Operating State / vector / tape) — beside the tall Risk rail |
| Market Kernel | main (chart) — beside the tall indicator/event rail |
| Symbol Lab | main (snapshot / chart / bars) — beside the tall position/news/regime rail |
| Analysis Workspace | side rail (regime / missing-data) — beside the tall 17-row universe table |

No data/contract change — markup only (panels moved between existing columns).

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web image): web build.

## ⚠ Visual baselines
Markup moved → the `@visual` baselines for these 4 tabs drift; the user
regenerates (`npm run test:visual:update`).

## Notes
- **Iteration 1.** The remaining 6 tabs (Mission Control, Risk Firewall, News,
  Catalyst, Trade Memory, System Ops) have different structures and need the same
  per-tab judgment of which region is empty — best done after viewing the result
  of these 4, since the work is blind here. Pair with the per-tab honesty roll-out.
