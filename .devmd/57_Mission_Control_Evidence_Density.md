# 57 — Mission Control Evidence Density

Date: 2026-05-28

## Goal

Reduce the lower Mission Control evidence density now that source, DB, and
capital-map state have stabilized. Keep the page read-only and focused on
reviewable portfolio evidence rather than trading actions.

## Implemented

- Replaced the four large lower evidence panels on Mission Control with a
  compact `mission-evidence-digest` section.
- Preserved the same API payload contract while presenting:
  - current interpretation verdict,
  - driver count and lead driver,
  - uncertainty count and lead conflict,
  - review/watchpoint count and lead watchpoint.
- Added responsive styling with fixed scan-card dimensions and line clamps so
  long evidence copy does not stretch the layout.
- Added Playwright coverage for the new Mission Control evidence digest.

## Verification

- `docker compose -f docker-compose.yml build web`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Mission Control renders"`
