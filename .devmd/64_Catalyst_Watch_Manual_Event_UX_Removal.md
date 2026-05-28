# 64 — Catalyst Watch Manual Event UX Removal

Date: 2026-05-28

## Goal

Remove the manual event registration surface from Catalyst Watch now that the
tab has a DB-backed read model path. Catalyst Watch should remain a review and
evidence surface, not a data-entry workspace.

## Implemented

- Removed the React `ManualEventEntry` form and its dedicated CSS.
- Removed the frontend manual-event POST helpers, seed helpers, and endpoint
  constants.
- Replaced the form with a read-only Event Catalog Evidence panel showing:
  calendar row count, confirmed dates, uncertain dates, and linked news count.
- Updated Catalyst Watch E2E and all-tabs structural contracts to expect the
  read-only evidence panel instead of manual entry.
- Kept the backend manual-event API contract intact for existing service and
  API regression coverage.

## Verification

- `docker compose -f docker-compose.yml build web`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_event_radar.py -q`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Catalyst Watch renders"`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/visual/all-tabs.visual.spec.ts -g "catalyst-watch renders required"`
