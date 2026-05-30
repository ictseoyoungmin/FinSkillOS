# 86 — db-unavailable Distinct State (Global Banner)

Date: 2026-05-30

## Goal

Slice 82 stamped the offline (`session is None`) path with
`systemStatus.db="MISSING"`, but every tab still renders the deterministic
fixture *shape* — so sample numbers could still be read as real data. Close that
confusion with an explicit, global "DB unavailable" state (vocab doc §1.3
target), without inventing per-tab minimal bodies or churning visual baselines.

## Implemented

- New `frontend/src/app/layout/OsDbUnavailableBanner.tsx` — returns `null`
  unless `dbStatus === "MISSING"`; otherwise renders a descriptive banner
  (`data-testid="db-unavailable-banner"`, `role="status"`): "Database
  unavailable. Tabs are showing sample shape, not live data. Connect a database
  or run a System Ops protocol to populate real data."
- `OsShell.tsx` renders the banner as the first child inside `<main>`, fed by
  the existing `/api/system-status` query's `dbStatus`. Placed inside the
  workspace (not the fixed 4-row shell grid) so an absent banner has zero layout
  impact.
- `os-shell.css` — sticky amber banner styling.

## Why this keying

`/api/system-status` is the authoritative DB-reachability signal (it already
reports `dbStatus="MISSING"` offline, Slice 14). Keying the banner there covers
the real outage case globally with one render site. The explicit
`X-FSO-Use-Fixture` demo override keeps `dbStatus="LIVE"`, so the banner never
appears during intentional demos or the forced-fixture visual baselines — hence
no baseline regeneration is needed.

## Tests

- `frontend/e2e/db-unavailable.spec.ts`:
  - route-mocks `/api/system-status` to `dbStatus="MISSING"` and asserts the
    banner is visible with the explicit copy;
  - asserts the banner is absent in the default (live DB) e2e stack.
- Visual suite re-run confirms no baseline drift (DB live in e2e → banner null).

## Notes

- This is the global, bounded form of the db-unavailable distinct state. A
  per-tab minimal "connect a database" body (replacing the sample shape entirely)
  remains a possible deeper follow-up, but the global banner already removes the
  "sample read as real" confusion.
- Descriptive only — "run a System Ops protocol" is operational, not execution
  wording.

## Verification

- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors (pre-existing ThemeProvider warning only)
- `docker compose --profile e2e run --rm e2e npx playwright test
  e2e/db-unavailable.spec.ts --workers=1` ✅ 2 passed
- `docker compose --profile e2e run --rm e2e npm run test:visual` ✅ baselines
  unchanged (banner absent under live DB)

## Known issues

- None specific to this slice. The pre-existing env-state
  `tests/test_api_system_ops.py::test_seed_sample_events_...` failure on the
  local persistent postgres is unrelated.
