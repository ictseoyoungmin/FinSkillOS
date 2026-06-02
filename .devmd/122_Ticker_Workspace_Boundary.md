# 122 — Ticker Workspace Boundary

Date: 2026-06-02

## Goal

Close D-007 from `.devmd/PROJECT_DIAGNOSTICS.md`: reduce the visual overlay
effect between the fixed ticker strip and the internally scrolling product
workspace.

## Scope

- Keep the shell structure unchanged: top tray, ticker strip, workspace, status
  bar.
- Improve the visual boundary between ticker strip and workspace content.
- Preserve responsive behavior and horizontal-overflow guarantees.

## Implemented

- Strengthened the ticker strip bottom border and added a subtle strip shadow.
- Added a workspace top border, inset boundary shadow, and a slightly larger top
  padding so page content begins below a clearer shell boundary.
- Adjusted the DB-unavailable banner margin to align with the new workspace top
  padding.
- Fixed narrow status-bar wrapping so shell chrome does not create horizontal
  overflow at the responsive audit viewport.
- Expanded responsive e2e coverage to assert the ticker/workspace boundary is
  present and does not introduce a visual gap.
- Updated `.devmd/PROJECT_DIAGNOSTICS.md` and `.devmd/CURRENT_STATE.md` so
  D-007 is recorded as complete.

## Tests

- `frontend/e2e/responsive.spec.ts` asserts:
  - no horizontal document overflow,
  - no element overflows the viewport,
  - ticker strip boundary shadow is present,
  - workspace top border/padding are present,
  - ticker and workspace remain directly adjacent.
- Full-scroll diagnostics are rerun to confirm all 10 routed tabs still render
  from top to bottom without console/page errors or horizontal overflow.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/responsive.spec.ts --project=chromium --workers=1
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/diagnostics/full-scroll-diagnostics.spec.ts --project=chromium --workers=1
```

Results:

- Web image build: passed.
- Frontend production build/type validation: passed.
- Focused responsive Playwright suite: 2 passed.
- Full-scroll diagnostic Playwright suite: 10 passed.

## Known Issues

- D-008 through D-010 remain queued in `.devmd/CURRENT_STATE.md`.
