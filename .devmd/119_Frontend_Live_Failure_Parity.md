# 119 — Frontend Live-Failure Parity

Date: 2026-06-02

## Goal

Close D-003 from `.devmd/PROJECT_DIAGNOSTICS.md`: product tabs that already have
live-backed API routes must not silently convert failed live reads into fixture
payloads. They may keep deterministic placeholder shapes for layout continuity,
but the UI must explicitly mark that shape as sample data when the live request
fails.

## Scope

- Align Control Room, Risk Firewall, Mission Control, News Intelligence,
  Catalyst Watch, Trade Memory, and the System Ops catalogue with the existing
  Market Kernel / Analysis Workspace live-failure contract.
- Preserve intentional forced-fixture visual paths used by Playwright baseline
  and diagnostic specs.
- Keep System Status fallback behavior because it powers the global
  DB-unavailable shell state.

## Implemented

- Removed snapshot-level silent fixture fallbacks from:
  - `frontend/src/features/control-room/api.ts`
  - `frontend/src/features/risk-guards/api.ts`
  - `frontend/src/features/portfolio/api.ts`
  - `frontend/src/features/news/api.ts`
  - `frontend/src/features/events/api.ts`
  - `frontend/src/features/system-ops/api.ts`
  - `frontend/src/features/trades/api.ts`
- Added explicit `StatusPill` live-failure indicators to the seven target pages.
- Passed the Control Room live-failure state into `ControlRoomGrid` so the
  warning appears inside the module surface.
- Expanded `frontend/e2e/live-fetch-pill.spec.ts` to cover all product snapshot
  tabs using the shared warning text.
- Updated `.devmd/PROJECT_DIAGNOSTICS.md` and `.devmd/CURRENT_STATE.md` so
  D-003 is recorded as complete.

## Tests

- `frontend/e2e/live-fetch-pill.spec.ts` now aborts each target snapshot API and
  verifies the module still renders with a visible live-data-unavailable pill.
- The same spec verifies no live-data-unavailable pill appears when the Docker
  API responds.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/live-fetch-pill.spec.ts --project=chromium --workers=1
```

Results:

- Web image build: passed.
- Frontend production build/type validation: passed.
- Focused Playwright live-failure suite: 18 passed.

## Known Issues

- D-004 through D-010 remain queued in `.devmd/CURRENT_STATE.md`.
