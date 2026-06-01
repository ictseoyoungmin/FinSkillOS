# 112 — Worker Auto-Start Orchestration + Test DB Isolation

Date: 2026-06-01

## Goal

(1) `docker compose up` should run web + api + worker + db together and work on a
fresh volume. (2) Stop the test suite from writing to the production DB — the
deeper root cause of the recurring mock sawtooth (Slice 111 found the structural
System Ops tests POST every protocol against the ambient DB, which in the Docker
api container is **production**).

## Implemented

### Orchestration (`docker-compose.yml`)
- New one-shot **`migrate`** service (api image, `alembic upgrade head`,
  `restart: "no"`, depends on `postgres: healthy`) so the schema is created /
  upgraded before app services start — a plain `docker compose up` now works on a
  fresh volume without a manual migration step.
- The **`worker`** service is out of the `worker` profile, so it starts with the
  default `up` (web + api + worker + db). It gains `restart: unless-stopped` and
  `depends_on` both `postgres: healthy` and `migrate: service_completed_successfully`.
- A failed worker cycle is logged and the loop continues; nothing is written on
  failure (Slice 111), so transient provider/network errors never corrupt data.

### Test DB isolation (`tests/conftest.py`)
- Autouse `_isolate_environment` points every test's `DATABASE_URL` at an
  **unreachable** address, so a test that does not set its own DB gets
  `session=None` (the offline / fixture path) instead of production. Locally
  psycopg is absent (already `None`); in the Docker api container psycopg +
  postgres are present, so without this every `docker compose run api pytest`
  wrote mock bars + sample rows into the live DB. Also forces the `mock` adapter
  (offline). Proven: a Docker `pytest` run leaves prod `mock` bars = 0.

### Deterministic audit ordering (`finskillos/db/models/system_ops.py`)
- `_utcnow` (the `created_at` default for the protocol-run / worker-cycle audit)
  is now strictly monotonic per process, so two runs in the same microsecond can
  no longer tie and flip `list_recent` order — removing the long-documented
  `test_seed_sample_events…` flake that the faster (isolated) tests surfaced.

### Test contract (`tests/test_operations_scripts.py`)
- The worker-contract test now asserts the new orchestration: no `worker`
  profile, `restart: unless-stopped`, `service_completed_successfully` (migrate
  gate), and the `alembic upgrade head` migrate command.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed.
- `docker compose config -q` ✅; default services now `postgres, migrate, api,
  web, worker` (app / e2e stay profiled).
- `docker compose up -d` → postgres healthy → migrate exits 0 → worker starts and
  runs a **real yahoo** cycle (13/13 tickers OK, news + indicators OK) with no
  mock and no duplication (NVDA stays 255 single-source).
- Docker `pytest test_api_system_ops test_operations_scripts` ×2 → all pass
  (flake gone) and prod `mock` bars stay 0.

## Known issues

- The worker still refreshes only on its interval + run-on-start; the
  request-driven Postgres job queue is Slice 113.
