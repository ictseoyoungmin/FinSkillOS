# 69 — Control Room Live Rail Composition

Date: 2026-05-28

## Goal

Reduce fixture-only overview rails in Control Room now that the detail tabs have
stable DB-backed read models. Control Room should compose a compact live
overview from stored market bars, Catalyst Watch events, symbol subscriptions,
mission state, and guard evidence without becoming the detailed source of truth.

## Implemented

- Replaced live Control Room ticker strip rows with latest stored market bars
  when available.
- Rebuilt the Portfolio / Market Tape rail from stored SPY and QQQ bars when
  enough history exists.
- Composed Catalyst Watch rail entries from the Event Radar read model.
- Composed Watchlist rail entries from active symbol subscriptions and latest
  stored close context.
- Updated data-state statuses so market tape, catalysts, and watchlist report
  `OK` or `MISSING` instead of hard-coded fixture `PARTIAL`.
- Updated Control Room copy to describe composed DB-backed rails and defer full
  evidence review to promoted detail tabs.
- Added API regression coverage proving live market, catalyst, and watchlist
  rails replace the fixture overview rows when DB rows exist.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_control_room.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/control_room.py tests/test_api_control_room.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Control Room is the default route"`
