# 123 — Lower Page Column Balance

Date: 2026-06-02

## Goal

Close D-008 from `.devmd/PROJECT_DIAGNOSTICS.md`: reduce large disconnected
empty regions in lower page screenshots caused by uneven fixed column grids.

## Scope

- Target the pages named in D-008: Control Room, Market Kernel, Catalyst Watch,
  and Trade Memory.
- Keep existing components, data contracts, and route behavior.
- Use responsive CSS only; do not change product semantics or add new cards.
- Preserve existing mobile single-column behavior.

## Implemented

- Control Room now converts the right rail into a full-width three-panel band at
  the desktop audit width.
- Market Kernel now moves the interpretation side rail below the main chart area
  as a three-panel band at the desktop audit width.
- Catalyst Watch now presents secondary interpretation/watchpoint/catalog
  evidence as a balanced lower band at the desktop audit width.
- Trade Memory now stacks the primary evidence flow before arranging secondary
  review/form content into a lower two-column band.
- Updated `.devmd/PROJECT_DIAGNOSTICS.md` and `.devmd/CURRENT_STATE.md` so
  D-008 is recorded as complete.

## Tests

- Full-scroll diagnostics are rerun for all 10 routed tabs to confirm top-to-
  bottom rendering, no console/page errors, and no horizontal overflow.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/diagnostics/full-scroll-diagnostics.spec.ts --project=chromium --workers=1
```

Results:

- Web image build: passed.
- Frontend production build/type validation: passed.
- Full-scroll diagnostic Playwright suite: 10 passed.

## Known Issues

- D-009 and D-010 remain queued in `.devmd/CURRENT_STATE.md`.
