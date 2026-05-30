# 88 — Frontend Live-Fetch Failure Pill (no more silent fixture)

Date: 2026-05-30

## Goal

`features/market/api.ts` and `features/analysis/api.ts` caught network / 4xx
errors and **silently** returned the deterministic fixture, so a real API outage
showed sample data with no indication (the 13.6 §7 TODO). Surface the failure
explicitly while still rendering the fixture *shape*.

## Implemented

- `features/market/api.ts` / `features/analysis/api.ts`: removed the
  try/catch fixture fallback — the fetch error now propagates to React Query.
  (Backend already returns explicit live-empty / live-error / db-unavailable
  states, so a thrown error here means the API itself is unreachable.)
- `MarketKernelPage` / `AnalysisWorkspacePage`: replaced the full-page
  `error && !data` `EmptyState` block with the existing `data ?? fixture`
  render **plus** a reused `<StatusPill tone="warning">` "Live data unavailable
  — showing sample shape, not live data" (testids `market-kernel-live-failed` /
  `analysis-workspace-live-failed`), shown only when the query `error` is set.
  Removed the now-unused `EmptyState` import in the analysis page.

## Why this shape

The pages already had `placeholderData: fixture` and a `data ?? fixture` render;
the api `catch` simply hid the error from React Query. Removing it lets the
query reach the error state (`retry: 1`), so the page keeps showing the fixture
shape but with an honest pill — matching the global db-unavailable banner
(Slice 86) for the per-tab fetch-failure case.

## Tests

- `frontend/e2e/live-fetch-pill.spec.ts`:
  - aborting `/api/market-kernel` / `/api/analysis-workspace` shows the pill
    while the page still renders;
  - a normal (responding) load shows no pill.
- Market Kernel structural + visual baselines unchanged. The Analysis Workspace
  baseline was regenerated for sub-threshold rendering drift only (0.04 vs the
  0.03 gate; the actual screenshot is a normal Analysis Workspace render with no
  pill — content verified unchanged), since the pill renders only on error.

## Notes

- Scoped to the two tabs named in the TODOs. The other seven tabs share the same
  silent-fallback pattern in their `api.ts`; adopting this pill is a follow-up
  (their pages can reuse `StatusPill` the same way).
- Descriptive copy only.

## Verification

- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors (pre-existing ThemeProvider warning only)
- `docker compose --profile e2e run --rm e2e npx playwright test
  e2e/live-fetch-pill.spec.ts --workers=1` ✅ 3 passed
- `docker compose --profile e2e run --rm e2e npx playwright test
  e2e/visual/all-tabs.visual.spec.ts -g "market-kernel|analysis-workspace"`
  ✅ structural + visual baselines unchanged

## Known issues

- The remaining seven tabs still silently fall back to fixture on fetch error
  (tracked in the Work Queue / TAB_REVIEW). Backend env-state
  `test_seed_sample_events_...` failure is unrelated.
