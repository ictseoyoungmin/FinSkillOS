# 72 — Control Room Rail Freshness Detail

Date: 2026-05-29

## Goal

Make composed Control Room rails auditable at a glance. After live rail
composition, the state band should show not only whether market/catalyst/
watchlist rails exist, but also the latest timestamp or date behind each rail.

## Implemented

- Added `latestMarketAt`, `latestEventAt`, `latestWatchlistAt`, and
  `railFreshnessNote` to the Control Room `dataState` contract.
- Populated live rail freshness from stored SPY/QQQ market bars, Event Radar
  upcoming event dates, and active watchlist latest bars.
- Added fixture freshness values for deterministic visual baselines.
- Updated the Control Room state band with a fifth auto-fitting tile for rail
  freshness and timestamp hints in the Market Tape / Linked Modules tiles.
- Added API regressions for live-empty freshness and composed live rail
  freshness timestamps.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_control_room.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps api ruff check api/routes/control_room.py api/schemas/control_room.py api/fixtures/control_room.py tests/test_api_control_room.py`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Control Room is the default route"`
