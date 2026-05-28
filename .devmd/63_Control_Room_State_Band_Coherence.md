# 63 — Control Room State Band Coherence

Date: 2026-05-28

## Goal

Make Control Room explicit about being a fixture-first operating overview now
that the underlying product tabs expose their own `dataState` contracts. The
overview should not imply that its summary cards are live DB-backed read
models.

## Implemented

- Added `dataState` to the `/api/control-room` response contract.
- Populated the fixture with overview, system, mission, market tape, guard,
  catalyst, and watchlist availability status.
- Added counts for market tape points, guards, catalysts, and watchlist rows
  so the UI can show compact evidence coverage.
- Added a Control Room state band for Overview Source, Evidence Coverage,
  Market Tape, and Linked Modules.
- Aligned the Control Room fixture guard count with the rendered guard stack.
- Added API and Playwright assertions for the state band contract.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_control_room.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Control Room is the default route"`
