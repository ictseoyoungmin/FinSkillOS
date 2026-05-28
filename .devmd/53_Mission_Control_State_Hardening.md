# 53 — Mission Control State Hardening

## Goal

Harden Mission Control after its DB-backed promotion.

The page should:

- make live vs fixture and DB state explicit in the first scan band;
- show sector and theme exposure state consistently, including empty states;
- avoid hiding data panels when live DB data is simply absent;
- keep all Mission Control copy descriptive and read-only;
- preserve existing capital-map and goal tracker test contracts.

## Out of Scope

- New brokerage, execution, or trading actions.
- Reworking Mission Control into a different product flow.
- Editing portfolio snapshots from the Mission Control tab.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_mission_control.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Mission Control renders"
```

## Implemented

- Added a compact Mission Control state band for source, DB, sector exposure,
  and theme exposure.
- Centralized live/fixture, DB, and exposure row state derivation inside the
  Mission Control page instead of scattering display logic across JSX.
- Kept both sector and theme exposure panels visible, including empty states,
  so live DB absence is explicit instead of looking like an unfinished layout.
- Added E2E coverage for the state band and always-visible theme exposure
  panel.
- Added an API regression test proving an empty reachable DB remains a live
  empty state instead of silently degrading to fixture copy.

## Verified

Docker-only checks passed:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_mission_control.py -q
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Mission Control renders"
```
