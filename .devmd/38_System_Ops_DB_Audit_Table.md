# 38 — System Ops DB Audit Table

## Status

Completed.

## Intent

Move System Ops protocol run history from local JSONL-only evidence into a
durable DB table so API, worker, and Mission Control-adjacent status views can
share the same operational audit trail.

## Scope

- Add `system_ops_protocol_runs` table.
- Add ORM model and repository.
- Store every live protocol run in the DB with protocol, status, message,
  detail, db status, source, and run timestamp.
- Keep the existing JSONL audit as a local fallback / sidecar.
- Make `GET /api/system-ops` read recent protocol runs and protocol
  `lastRunAt` from DB when available.
- Add tests for DB persistence and readback.

## Non-Goals

- No new UI layout redesign.
- No worker status dashboard yet.
- No deletion/retention policy beyond newest-first reads.

## Implementation

- Added `system_ops_protocol_runs` ORM model, repository, and Alembic
  migration `0011_system_ops_protocol_runs`.
- Live protocol POSTs now persist a DB audit record and still append the
  existing JSONL sidecar.
- `GET /api/system-ops` reads recent protocol runs from DB when reachable,
  falls back to JSONL otherwise, and fills each protocol card `lastRunAt`
  from the latest DB row.
- The existing fixture override remains available through
  `X-FSO-Use-Fixture: 1`.

## Verification

- `python3 -m ruff check api/routes/system_ops.py finskillos/db/models/system_ops.py finskillos/db/repositories/system_ops_repo.py finskillos/db/migrations/versions/0011_system_ops_protocol_runs.py tests/test_api_system_ops.py tests/integration/test_db_migrations.py`
- `timeout 90 python3 -m pytest tests/test_api_system_ops.py tests/integration/test_db_migrations.py`
- `docker compose -f docker-compose.yml --profile worker up -d --build api worker`
- `docker compose -f docker-compose.yml exec -T api alembic upgrade head`
- `curl -s -X POST http://localhost:8000/api/system-ops/seed-sample-account`
- `curl -s http://localhost:8000/api/system-ops`

## Live Result

The local Postgres DB was migrated from `0010_symbol_logo_cache` to
`0011_system_ops_protocol_runs`. A live seed protocol run was persisted and
`GET /api/system-ops` now returns:

- `source: live`
- latest `recentProtocolRuns[0].source: live`
- `recentProtocolRuns[0].dbStatus: LIVE`
- `protocols[].lastRunAt` for `seed_sample_account`
