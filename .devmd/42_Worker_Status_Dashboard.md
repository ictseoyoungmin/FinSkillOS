# 42 — Worker Status Dashboard

## Goal

Make the lightweight refresh worker observable from System Ops.

The system should:

- persist each completed worker cycle as an audit record;
- expose latest and recent worker cycle state in `GET /api/system-ops`;
- summarize market, news, and indicator cycle health without implying trading
  action;
- keep existing protocol audit rows intact;
- keep Docker worker configuration explicit and folder-scope aware.

## Design

The worker already returns a structured cycle summary. This slice promotes that
summary into a durable read model:

```text
scripts/refresh_worker.py cycle summary
  -> worker_cycle_runs table
  -> System Ops workerStatus payload
  -> React Worker Status panel
```

The dashboard is intentionally operational:

- latest cycle status and timestamp;
- latest market/news/indicator sub-statuses;
- recent cycle history;
- folder refresh scope metadata when present.

It does not start, stop, or schedule the worker. Process lifecycle remains a
Docker/ops concern.

## Implemented

- Add a `worker_cycle_runs` model, repository, and Alembic migration.
- Persist successful `run_cycle` summaries from `scripts/refresh_worker.py`.
- Extend System Ops schemas and route payload with `workerStatus`.
- Render a compact Worker Status panel in the System Ops React page.
- Add focused API, migration, and operations-script tests.
- Add `FINSKILLOS_REFRESH_FOLDER_NAMES` to Compose API/worker environments.

## Out of Scope

- Start/stop/restart controls from the UI.
- Per-folder worker intervals.
- Live process supervision or heartbeat polling.
- Deleting or compacting historical worker cycle rows.

## Validation

```bash
python3 -m ruff check api/routes/system_ops.py api/schemas/system_ops.py scripts/refresh_worker.py finskillos/db/models/system_ops.py finskillos/db/repositories/system_ops_repo.py tests/test_api_system_ops.py tests/test_operations_scripts.py tests/integration/test_db_migrations.py
timeout 90 env FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_system_ops.py tests/test_operations_scripts.py tests/integration/test_db_migrations.py -q
docker compose build api web worker
docker compose up -d postgres api web
docker exec finskillos-api alembic upgrade head
docker compose --profile worker up -d worker
```
