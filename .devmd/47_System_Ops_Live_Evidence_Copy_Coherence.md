# 47 — System Ops Live Evidence Copy Coherence

## Goal

Make the top System Ops evidence panels match the current live DB-backed state.

The system should:

- avoid live pages claiming the data layer is still fixture-first;
- compute protocol count from the actual protocol catalogue;
- keep fixture-forced responses explicit about fixture status;
- preserve the read-only / descriptive-only safety language.

## Context

After Slice 45 and Slice 46, the lower System Ops status panels report:

```text
DB LIVE
Source LIVE
Completeness COMPLETE
Database LIVE
Market / Indicators LIVE
News / Event Stores LIVE
```

The top evidence panels still showed fixture-era copy:

```text
Data layer: Fixture
Market, event, and news stores remain fixture-first.
The cockpit can run locally, but source freshness is limited.
```

That copy is correct only for fixture-forced responses.

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

- Live `GET /api/system-ops` now updates the top evidence bundle together with
  the live data-source pills.
- The live trust header now reports `Local System DB-Backed` instead of
  `Local System Usable with Partial Data`.
- `Protocols` is computed from the actual protocol catalogue, so it now reports
  `7` instead of the stale hard-coded `6`.
- The live data-layer driver now reports `Live`.
- Fixture-forced responses still keep fixture-era copy, which is correct for
  explicit fixture mode.

## Verified

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker exec finskillos-api python -c "..."
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
docker compose -f docker-compose.yml --profile e2e run --rm e2e node -e "..."
```

Live API spot-check:

```text
source=live
judgment=Local System DB-Backed and Ready for Read Ops
drivers=[Protocols=7, Data layer=Live, Mode=Read]
conflicts=[Stored data vs provider freshness, Protocol actions vs trading actions]
fixture-first absent from rendered page body
```
