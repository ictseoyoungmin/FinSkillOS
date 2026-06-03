# 146 — Worker Queue Visibility / Recovery UI (Phase 1)

**Status:** Done.

Operators could see worker *cycles* (cadence) but not the underlying *job queue*
(queued/running/done/error), and had no way to recover a failed refresh except
re-clicking the protocol or waiting for the next cadence. Surfaces the queue +
adds a one-click retry.

## Implemented
- **API GET `/api/system-ops`** — `workerStatus` now carries `job_counts`
  (by status) and `recent_jobs` (last 10): id, jobType, status, requestedBy,
  folderId (from payload), created/finished, a truncated `error`, and `retryable`
  (terminal = DONE/ERROR). Built from the existing
  `WorkerJobRepository.count_by_status()` / `list_recent()`.
- **API POST `/api/system-ops/worker-jobs/{id}/retry`** — re-enqueues a fresh job
  of the same `job_type` (carrying the original `folder_id` scope + a current
  runtime-settings snapshot, same dedup_key so it's idempotent). 404 unknown id,
  409 if the job is still active (QUEUED/RUNNING — nothing to recover). Returns the
  refreshed `WorkerStatusSummary`.
- **Frontend** — System Ops → Worker Status gains a "Job Queue" panel: status-
  colored rows (queued/running/done/error), folder-scoped marker, requestedBy,
  timestamp, truncated error, and a **Retry/Re-run** button on terminal jobs that
  calls the retry endpoint and refreshes the page. Badge shows the status roll-up.

## Tests
- `tests/test_api_system_ops.py`: a failed `refresh_market` job is visible
  (`jobCounts.ERROR == 1`, row `retryable`, error starts with the class name);
  retry creates a fresh QUEUED `refresh_market`; unknown id → 404.

## Verification
- Offline: system-ops + worker-jobs tests PASS; ruff clean; frontend
  `npm run build` + `npm run lint` clean.
- Docker: api pytest (system-ops + worker-jobs + v42 contract) + `build api web`.

## Note
- Retry re-enqueues a *new* job (the queue is the unit of work); it does not mutate
  the failed row. Pairs with the runbook's "Recover" section (slice 145). Provider
  auto-retry/backoff (so fewer manual retries are needed) is slice 148.
