# 67 — Catalyst Watch Backend Mutation Boundary Cleanup

Date: 2026-05-28

## Goal

Make Catalyst Watch / Event Radar a read-only product-tab boundary by removing
backend mutation routes that were left behind after the manual-event UI was
removed. Event ingestion stays under System Ops operational protocols.

## Implemented

- Removed `POST /api/event-radar/manual-event`.
- Removed `POST /api/event-radar/seed-sample-events`.
- Removed manual-event input/result/rules schemas from the Event Radar API
  contract.
- Removed `manualEntryRules` from the API response, frontend type, and fixture.
- Preserved `POST /api/system-ops/seed-sample-events` as the event ingestion
  protocol boundary.
- Added an OpenAPI regression proving Event Radar exposes no mutation routes
  while the System Ops seed protocol remains available.
- Removed the frontend E2E request that exercised the retired manual-event
  route.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_event_radar.py tests/test_api_system_ops.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/event_radar.py api/schemas/event_radar.py api/fixtures/event_radar.py tests/test_api_event_radar.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Catalyst Watch renders"`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"`
