# 124 — Control Room Nested Scroll Cleanup

Date: 2026-06-02

## Source Queue Item

D-009 in `.devmd/CURRENT_STATE.md`:

> Control Room nested-scroll cleanup — Remove or constrain nested column scroll
> behavior inside the already scrollable OS workspace.

## Scope

- Remove independent vertical scroll ownership from the three Control Room
  content columns.
- Keep the Slice 123 lower-page column balance behavior for the 981–1320px
  audit width.
- Collapse duplicate Control Room breakpoint declarations left by prior
  responsive slices.
- Do not alter data contracts, copy, or non-Control Room routes.

## Implementation

- `frontend/src/pages/control-room/control-room-grid.css`
  - Changed `.fso-control-column` from `overflow-y: auto` to `overflow:
    visible`.
  - Removed scrollbar compensation padding from the columns.
  - Added `min-width: 0` so nested cards can shrink within grid columns without
    horizontal overflow.
  - Removed the duplicate 981–1320px media query and retained one middle-width
    layout rule for the right rail.
  - Ensured the right rail returns to normal stacked flow below 1180px/980px.
- `frontend/e2e/responsive.spec.ts`
  - Added a Control Room regression assertion that all three columns keep
    `overflow-x` and `overflow-y` visible, leaving scroll ownership with the OS
    workspace.

## Verification

Docker checks:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/responsive.spec.ts --project=chromium --workers=1
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/diagnostics/full-scroll-diagnostics.spec.ts --project=chromium --workers=1
```

## Result

- Web image build: passed.
- Frontend production build/type validation: passed.
- Responsive Control Room e2e: 2 passed.
- Full-scroll diagnostic Playwright suite: 10 passed.
- Control Room diagnostic JSON reported no document or workspace horizontal
  overflow after the column scroll cleanup.

## Notes

- D-010 remains queued in `.devmd/CURRENT_STATE.md`.
