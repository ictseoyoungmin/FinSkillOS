# 66 — Control Room DB Read Model Promotion

Date: 2026-05-28

## Goal

Promote `/api/control-room` from a fixture-first overview to a DB-backed
operating overview when a database session is reachable, without pretending
that every overview rail is live.

## Implemented

- Wired the API route to `build_control_room_view_model` for live mission,
  portfolio, regime, and risk-guard context.
- Preserved `X-FSO-Use-Fixture: 1` and `/api/mock/control-room` as deterministic
  fixture paths for visual baselines.
- Added live empty-state behavior when the DB is reachable but no account
  baseline exists.
- Mapped live mission progress, operating state, sector exposure, review queue,
  interpretation cards, and risk firewall rows into the existing React schema.
- Kept ticker strip, catalyst, watchlist, and market tape rails as overview
  context while marking them partial in `dataState`.
- Added live-empty and live-seeded API regression coverage.

## Verification

- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_control_room.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/control_room.py tests/test_api_control_room.py`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Control Room is the default route"`
