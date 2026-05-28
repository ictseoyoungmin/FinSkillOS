# 45 — System Ops Data Source State Clarity

## Goal

Make System Ops data-source state visually unambiguous when the API is reading
from the live DB.

The system should:

- avoid showing `Database: Fixture` beside `DB LIVE` status-bar pills;
- align System Ops data-source pills with the live/fixture source of the page;
- keep Market / Indicators and News / Event Stores honest about stored-data
  readiness without implying external provider freshness;
- preserve descriptive/read-only wording.

## Context

After Slice 43, System Ops overview can show:

```text
Status bar: Data source LIVE · DB LIVE
Data source strip: Database FIXTURE · Fixture-first in Slice 13.8
```

This is confusing. The route starts from the fixture catalogue and then overlays
live audit/worker state, but the visual pills should describe the final payload
state the user is seeing.

## Out of Scope

- New provider integrations.
- New data-source health tables.
- Worker start/stop/schedule controls.
- Trading-action wording or controls.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
```

## Implemented

- `GET /api/system-ops` now replaces fixture data-source pills with live
  DB-backed pills when a DB session is active.
- The live data-source strip reports:
  - `Database: LIVE`
  - `Market / Indicators: LIVE`
  - `News / Event Stores: LIVE`
  - `Mode: LIVE`
- Fixture-forced responses still preserve `Database: FIXTURE`, so fixture mode
  remains explicit.
- Live details avoid provider freshness claims; they say stored data is read
  from the live DB and freshness is shown by refresh/status signals.

## Verified

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
docker exec finskillos-api python -c "..."
```

Live API spot-check:

```text
source=live
Database=LIVE
Market / Indicators=LIVE
News / Event Stores=LIVE
Mode=LIVE
```
