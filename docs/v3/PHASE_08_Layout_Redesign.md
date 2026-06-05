# Phase 8 — Layout / Information-Density Redesign

Spec: [REAL_DATA_AND_LAYOUT_SPEC.md](REAL_DATA_AND_LAYOUT_SPEC.md) §Phase 8.

**Goal:** per-tab top→bottom layout efficiency — cut wasted vertical space,
tighten hierarchy (judgment + key numbers above the fold; detail behind
disclosure), share components, reflow responsively. Layout/CSS only — no behavior
or contract change.

## Candidate slices

- **Layout-audit doc** — per-tab before/after intent, grounded in top+bottom
  captures; ranks tabs by wasted space (from the captures: Ops protocol history,
  Control Room evidence stack, Mission Control are early candidates).
- **Per-tab redesign slices** — densify tabular stacks into tables, collapse dead
  gutters, move drilldowns behind `<details>`, unify on `Panel` / `SectionHeader`
  / evidence panels. One slice per tab (or grouped by similarity).
- **Visual-baseline regen pass** — once layouts settle, regenerate the Playwright
  `@visual` baselines (needs browser binaries — env-blocked here).

## Dependencies

Independent of Phase 7, but do the Phase-7 audit first so layout doesn't entrench
a card that should be an explicit empty-state.

## Verification

- Frontend: tsc + vite build + eslint.
- **Visual baselines:** each layout slice states (a) regen here (where Playwright
  browsers exist) or (b) gate new structure so fixture renders are unchanged until
  a dedicated regen pass. The repo currently can't run Playwright (see
  CURRENT_STATE "Standing open"), so prefer (b) or batch the regen.
- Docker gate (rebuild web first).

## Constraints

- Markup/CSS only; read models untouched (keeps Phase-7 honesty valid).
- Reuse existing shared UI; avoid new bespoke one-off layouts.
