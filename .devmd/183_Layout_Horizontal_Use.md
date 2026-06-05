# 183 — Use Horizontal Space on Mission / Risk / Catalyst (v3 Phase 8)

**Status:** Done. Fixes the user-flagged "행 위주로 나눠 비효율" — content stacked
into one tall column leaving the other half of the row empty (News is the good
reference: balanced multi-column rows).

## Fixes

### Mission Control
- The `PortfolioEditorPanel` was the whole of a narrow grid column, so column 1
  was enormously tall while columns 2–3 (milestone, exposure) ended early →
  **the entire right half was empty**. Moved the editor out of the 3-column grid
  into its **own full-width row** (`fso-mission-control-editor-row`); its
  `auto-fit` form grids now spread across the width. The 3-column grid above is
  now balanced (snapshot+constraint · milestone · exposure).

### Risk Firewall
- The guard ladder (8 cards) was a single tall column; alerts + protocol were
  short → void on the right. Restructured to a **2-column layout**: the guard
  ladder beside a **side column** that stacks alerts + protocol + interpretation +
  watchpoints. `GuardResultCard` now lays guards in a **responsive 2-col grid**
  (`guard-result-card.css`), halving the ladder height.

### Catalyst Watch
- col 1 held 4 tall panels (tables + the long linked-news list); col 2 (interp +
  watchpoints + catalog) was short → void. Moved the **long linked-news list into
  col 2** so it fills the side column beside the taller event tables.

Markup/CSS only — no data/contract change.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web image): web build.

## ⚠ Visual baselines
Drifts the `@visual` baselines for Mission / Risk / Catalyst; the user
regenerates (`npm run test:visual:update`).

## Notes
- Remaining: System Ops (the protocol-run history the user flagged earlier) +
  Trade Memory. Same principle — spread content horizontally; don't leave a half
  empty. Then the Phase-7 honesty roll-out.
