# 113 — Postgres Worker Job Queue (request-driven worker)

Date: 2026-06-01

## Goal

The worker should idle, then process work from a Postgres job queue (so a request
can wake it), alongside the interval refresh — with no duplicate work.

## Implemented

- **Model + migration** — `WorkerJob` (`finskillos/db/models/system_ops.py`,
  Alembic `0013_worker_jobs`): `job_type`, `status`
  (QUEUED/RUNNING/DONE/ERROR), `dedup_key`, `requested_by`, `payload`, `result`,
  `error`, monotonic `created_at`, `started_at`, `finished_at`. Job types:
  `refresh_all` / `refresh_market` / `refresh_news` / `calculate_indicators`.
- **Repository** `WorkerJobRepository`:
  - `enqueue` is **idempotent** on `(job_type, dedup_key)` while a job is still
    active (QUEUED/RUNNING) — a request never piles up duplicate work.
  - `claim_next` atomically claims the oldest QUEUED job (postgres
    `FOR UPDATE SKIP LOCKED` so concurrent workers never double-claim; plain
    select on sqlite for tests), marking it RUNNING.
  - `complete` / `fail` / `get` / `list_recent` / `count_by_status`.
- **Worker** (`scripts/refresh_worker.py`): the daemon is now queue-driven —
  `enqueue_refresh` (on start + every interval, dedup-safe) and `drain_queue`
  (each poll tick, default `FINSKILLOS_WORKER_POLL_SECONDS=5`) which claims a
  job, runs the matching refresh (`_config_for_job` enables only the relevant
  sub-refresh, then `run_cycle`), and records DONE / ERROR with the summary on
  the job row. `--once` keeps the original single direct cycle (test contract).
  Upserts mean reruns never duplicate bars.
- `docker-compose.yml` worker gains `FINSKILLOS_WORKER_POLL_SECONDS`.

## Tests (`tests/test_worker_jobs.py`)

- enqueue idempotency (active dedup → same row; finished → new row);
- `claim_next` FIFO + RUNNING + never re-claims a running job;
- `fail` records the error; `drain_queue` processes a `refresh_market` job
  (mock adapter, writes SPY bars, job → DONE with summary); an unknown job_type
  → ERROR.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed.
- `alembic upgrade head` applies `0013` (worker_jobs table present).
- Docker `pytest test_worker_jobs test_operations_scripts test_api_system_ops`
  (`--no-deps`) ✅ + ruff ✅.
- **Live end-to-end**: `docker compose up` → the worker enqueued a `refresh_all`
  job (`requested_by=worker_start`), claimed + processed it → `status=DONE` with
  the cycle summary; prod `mock` bars = 0, NVDA = 255 (no duplication).

## Known issues

- The **request** path (System Ops refresh buttons enqueue a job instead of
  running synchronously) + the frontend QUEUED handling is Slice 114. Note: a
  plain `docker compose up` after pulling new migrations needs the `migrate`
  image rebuilt (`docker compose build` / `up --build`), since it is a separate
  image from `api`.
