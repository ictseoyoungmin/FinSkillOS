# 48 — Worker Cadence Supervision

## Goal

Make Worker Status show whether the refresh worker is still on schedule.

The system should:

- derive a worker cadence state from the latest completed cycle;
- expose expected next-cycle timing in `GET /api/system-ops`;
- distinguish missing history, cycle errors, fresh cadence, and stale cadence;
- keep lifecycle controls out of the UI;
- preserve descriptive/read-only wording.

## Design

This slice does not inspect Docker process state or start/stop containers.
Instead, it uses the persisted `worker_cycle_runs` read model:

```text
latest finished_at
  + FINSKILLOS_WORKER_INTERVAL_SECONDS
  + FINSKILLOS_WORKER_STALE_GRACE_SECONDS
  -> cadenceStatus
```

Default interval remains 24 hours. Default grace is half the interval, with a
minimum of 60 seconds.

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

- `WorkerStatusSummary` now includes:
  - `cadenceStatus`
  - `expectedNextCycleAt`
  - `cadenceDetail`
- `GET /api/system-ops` derives cadence from the latest `worker_cycle_runs`
  row using `FINSKILLOS_WORKER_INTERVAL_SECONDS` and
  `FINSKILLOS_WORKER_STALE_GRACE_SECONDS`.
- Cadence states:
  - `FRESH`: latest cycle is still within interval + grace.
  - `STALE`: latest cycle is overdue.
  - `ERROR`: latest cycle failed.
  - `MISSING`: no assessable cycle exists.
- System Ops Worker Status tab now shows cadence and next due timing in the
  compact metrics row.
- Timestamp handling normalizes DB-returned naive datetimes to UTC so SQLite
  tests and Postgres runtime behave consistently.

## Verified

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py -q
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
docker exec finskillos-api python -c "..."
```

Live API spot-check:

```text
worker status=OK
cadenceStatus=FRESH
expectedNextCycleAt=2026-05-28T08:31:41.979921+00:00
cadenceDetail=On cadence; expected every 86400s with 43200s grace.
```
