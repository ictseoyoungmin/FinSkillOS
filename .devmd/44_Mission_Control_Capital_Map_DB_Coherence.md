# 44 — Mission Control Capital Map DB Coherence

## Goal

Restore Mission Control's capital-map contract when the page reads from the
live DB-backed API payload.

The system should:

- keep the Mission Control page rendering the capital-map sector panel;
- preserve fixture and DB-backed payload shape for e2e stability;
- avoid placeholder/TBD data;
- keep the page descriptive and read-only.

## Context

Slice 43 validation left one unrelated e2e failure:

```text
Mission Control renders goal tracker and milestone timeline
  -> missing data-testid="mission-capital-map-sector"
```

The failure appears only against the current running DB-backed payload. The
next step is to harden the Mission Control read model so live/fixture payloads
keep the same UI contract.

## Out of Scope

- New portfolio editing workflows.
- New broker/account integrations.
- Trading-action language or controls.
- Reworking Mission Control layout beyond the missing capital-map contract.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_mission_control.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Mission Control renders"
```

## Implemented

- Restored the `mission-capital-map-sector` test contract on the Mission
  Control page while preserving the existing `capital-map` panel test id used by
  visual smoke checks.
- Added an explicit empty state inside `CapitalMapPanel` for DB-backed accounts
  without exposure rows.
- Kept the Mission Control capital map read-only and descriptive.

## Verification

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_mission_control.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "Mission Control renders"
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts
```

Result:

- Docker API Mission Control tests passed: 9 tests.
- Docker frontend build passed.
- Docker Mission Control targeted e2e passed: 1 test.
- Docker Risk / Mission / Ops e2e passed without exclusions: 5 tests.
