# 130 — Collection Control Frontend (W-4)

**Status:** Done (one follow-up: visual baseline regen).

W-4 of folder-driven collection control. Replaces the hand-typed ticker text
fields with a GUI surface in the System Ops module, wired to the slice-129 API.

## Implemented
- **New `features/collection-control/` module** — `types.ts`, `api.ts` (GET +
  PATCH flags + create/delete folder + add/remove symbol + global-toggle, each
  returning the full refreshed snapshot), and
  `components/CollectionControlPanel.tsx`.
- **System Ops "Collection Control" tab** (`SystemOpsPage.tsx`) between Overview
  and Runtime Settings (`data-testid="system-ops-tab-collection"`). The panel
  shows:
  - a totals roll-up (active folders, per-type effective symbol counts);
  - a global toggle row (Active / Price / Indicators / News across all folders);
  - a create-folder form;
  - folder cards — name + System badge + member count, member chips with a remove
    `×`, an add-ticker input (subscribe + link in one call), the four per-folder
    checkboxes, and a Delete button disabled for the protected System folder;
  - inactive / all-types-off warnings (honest "not collecting" states);
  - the descriptive safety caption.
- **Removed** the `FINSKILLOS_MARKET_REFRESH_TICKERS` /
  `FINSKILLOS_INDICATOR_REFRESH_TICKERS` runtime-settings fields — the universe is
  no longer hand-typed. Other Market knobs (adapter, timeframe, refresh folders)
  stay.
- `collectionControl.fixture.ts` placeholder (System folder + 22 leaders) so the
  panel renders deterministically before the live fetch resolves.
- Endpoint `collectionControl` added to `endpoints.ts`; CSS in `system-ops.css`.

## State / UX
- React Query `["collection-control"]`; every mutation `setQueryData`s the full
  returned snapshot so the whole surface re-renders consistently. Tone-coded notice
  (success/error/info) surfaces API errors (e.g. System-folder delete → 409). Live
  fetch failure shows the standard "sample shape, not live data" pill.

## Verification
- `npm run build` (tsc -b + vite) PASS; `npm run lint` clean (only the pre-existing
  ThemeProvider fast-refresh warning).
- Docker: `docker compose build web` (production image runs the same build) PASS.
- Functional e2e `risk-mission-ops.spec.ts` unaffected (it clicks the Worker tab
  and checks protocol cards / caption — both unchanged).

## Known follow-up
- **Visual baseline regen required:** `e2e/visual/all-tabs.visual.spec.ts`'s
  `system-ops.png` baseline drifts because the tab bar gained a "Collection Control"
  tab and the Runtime tab lost two fields. Regen needs Playwright browsers
  (unavailable in this environment) — run `npm run test:e2e -- --update-snapshots`
  for the system-ops visual case. No functional behavior depends on it.

## Follow-ups (W-5)
- Symbol-Lab "add to folder" cross-link (idea U1); per-folder open/collapse focus;
  coverage/freshness chips (how many members have stored bars); confirm+undo on
  destructive removal (idea U9).
