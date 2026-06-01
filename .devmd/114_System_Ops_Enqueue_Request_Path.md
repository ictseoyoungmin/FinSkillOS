# 114 — System Ops Refresh Enqueues Jobs (request path)

Date: 2026-06-01

## Goal

Complete the request-driven side of the Slice-113 queue: the System Ops refresh
buttons should **enqueue a worker job** (a request) instead of running the
refresh synchronously, so the API never blocks on a provider call and the worker
does the work.

## Implemented

- `api/schemas/system_ops.py`: `ProtocolStatus` gains `QUEUED`.
- `api/routes/system_ops.py`: the three provider-touching protocols now enqueue
  via a shared `_enqueue_refresh_job` (idempotent on the job type,
  `requested_by="system_ops"`) and return `QUEUED` with `job_type` + `job_id` in
  `detailEvidence`:
  - `refresh-market-data` → `refresh_market`
  - `refresh-news` → `refresh_news`
  - `calculate-indicators` → `calculate_indicators`
  The synchronous refresh logic is removed from the route (the worker's
  `run_cycle` already owns it). The DB-only protocols (seed account / regime /
  risk guards / events) stay synchronous. No reachable DB → still `NOOP`
  (`no_database_session`), never a production write.
- Frontend: `ProtocolStatus` type + a `--queued` result style
  (`protocol-card-item.css`, cyan) so the cockpit renders the QUEUED outcome.

## Tests (`tests/test_api_system_ops.py`)

- The three refresh protocols now assert `QUEUED` + a `worker_jobs` row of the
  right `job_type` (`requested_by="system_ops"`) and that the API did **not**
  run the work itself (no bars / news / indicators written).
- New idempotency test: two `refresh-market-data` POSTs return the same `job_id`
  and leave exactly one `QUEUED` row (no duplicate work).
- The execution of those refreshes is covered at the worker level (Slice 113
  `drain_queue` + the operations-scripts cycle tests).

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed.
- `ruff` ✅; web `npm run build && lint` ✅ (0 errors).
- Docker pytest (system_ops + worker_jobs + v42 contract, `--no-deps`) ✅.
- **Live end-to-end**: `POST /api/system-ops/refresh-market-data` → `QUEUED`
  (job_queued, job_id); the running worker claimed the `refresh_market` job
  (`requested_by=system_ops`) → `DONE`; prod `mock` bars = 0 (no duplication).

## Docs

- New living spec `docs/WORKER_QUEUE_AND_API_SPEC.md` (orchestration, worker,
  job queue, request path, env, testing guarantees) — to be updated as the
  worker/queue/API evolve.

## Known issues

- None. Completes the P0 orchestration arc (111–114). The static System Ops
  visual baseline is unchanged (QUEUED styling only appears on a clicked result).
