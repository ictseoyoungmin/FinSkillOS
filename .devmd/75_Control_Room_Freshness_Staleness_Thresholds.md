# 75 — Control Room Freshness Staleness Thresholds

Date: 2026-05-29

## Goal

Promote Control Room rail freshness from timestamp-only evidence to explicit
fresh/stale/missing classification. The overview should show whether market,
catalyst, and watchlist rails are current enough to support the composed read.

## Implemented

- Added per-rail freshness statuses to the Control Room `dataState` contract:
  `marketFreshnessStatus`, `catalystFreshnessStatus`, and
  `watchlistFreshnessStatus`.
- Added aggregate `railFreshnessStatus` with `FRESH`, `STALE`, and `MISSING`
  vocabulary.
- Classified market/watchlist rails as stale when the latest stored bar date is
  more than three days behind the generated overview date.
- Classified catalyst freshness from the next event date, treating missing
  event rails as explicit `MISSING`.
- Updated the Control Room state band to render the API freshness status rather
  than deriving `COMPLETE/PARTIAL` from timestamp presence in React.
- Added API regression coverage for fixture freshness, live-empty missing
  freshness, fresh composed rails, and stale market/watchlist rails.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_control_room.py -q`
- `docker compose -f docker-compose.yml run --rm api python -m ruff check api/schemas/control_room.py api/routes/control_room.py api/fixtures/control_room.py tests/test_api_control_room.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Control Room is the default route"`

## Notes

- The wording remains descriptive and operational. No brokerage, order, or
  direct trading-action language was introduced.
