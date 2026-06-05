# 181 — Shared Panel Density Pass (v3 Phase 8)

**Status:** Done. Opens Phase 8 (layout) with the highest-leverage **even**
improvement: every tab uses the shared `Panel`, so tightening its chrome
densifies all 10 tabs at once (user's "전체 탭 균등" direction).

## Implemented

### `frontend/src/shared/ui/panel.css`
- Panel head padding `9px 14px → 8px 12px`.
- Panel body padding `14px 16px → 12px 14px`, gap `12px → 10px` (~15% tighter).

Conservative, objective density win — no structural/markup change, no behavior
change. Cuts a few px of vertical chrome from every panel on every tab.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker (rebuilt web image): web build.

## ⚠ Visual baselines
This changes shared panel spacing, so it **drifts every Playwright `@visual`
baseline**. Per the user's direction, the user regenerates baselines where
Playwright browsers exist:

```bash
cd frontend && npx playwright install --with-deps chromium
npm run test:visual:update      # regenerate all @visual snapshots
git add frontend/e2e/**/*-snapshots/** && git commit -m "chore: regen visual baselines (181 density)"
```

## Notes
- Next (Phase 8 structural): per-tab redensification — tabularize the long
  card-per-row stacks the user flagged (Ops protocol-run history; Control Room
  evidence stack), move detail behind disclosure, tighten dead gutters. These are
  per-tab slices; with the user regenerating baselines they can change fixture
  layout directly. Pair with the Phase-7 per-tab honesty roll-out (181+ OriginTag
  on derived values / explicit empty-states).
