# 134 — Per-Folder "Refresh Now" (idea F3)

**Status:** Done. Backend (policy + worker + API) + frontend.

Promotes ideas-backlog **F3**. Lets an operator enqueue a worker refresh scoped to
a single folder's members instead of waiting for the next cadence — pairs with the
slice-133 "add to folder" flow (track a symbol, then refresh it on demand).

## Implemented
- **Policy scope** (`build_watchlist_refresh_policy`) — new `folder_id` param.
  With `collection_type` + `folder_id`, the universe is *only* that one folder's
  members (subject to its active state + matching type flag); the env base universe
  is **not** unioned (a scoped run collects just that folder). Scope string becomes
  `collection:<type>:folder=<id>`. `_flagged_folder_tickers` gained the filter.
- **Worker** (`scripts/refresh_worker.py`) — `WorkerConfig.refresh_folder_id`;
  `run_cycle` threads it into the market/indicator/news policy builds;
  `drain_queue` reads `folder_id` from the claimed job payload
  (`_extract_folder_scope_from_job_payload`) and sets it on the effective config.
- **API** — `POST /api/system-ops/collection-control/folders/{id}/refresh`
  idempotently enqueues a `refresh_all` worker job with payload
  `{folder_id, runtime_settings}` and `dedup_key=refresh_all:folder=<id>` (per-folder
  dedup, so distinct folders queue independently and a re-click while pending
  returns the same job). Unknown folder → 404. Returns the refreshed snapshot.
- **Frontend** — `refreshFolder()` API + a per-folder "Refresh now" button (in a
  new card-actions row, disabled when the folder is inactive); the notice shows
  "Refresh queued for <folder>".

## Dialect gotcha caught in live testing (fixed in this slice)
- The folder-scoped audit label `collection:<type>:folder=<uuid>` (~63 chars)
  overflowed the `worker_cycle_runs.{market,news,indicator}_scope` `VARCHAR(32)`
  columns. **SQLite ignores VARCHAR length so the offline tests passed**, but the
  live worker hit `StringDataRightTruncation` on Postgres and every scoped job
  ended ERROR (the collection itself succeeded; the *audit insert* failed). Fix:
  widen the three columns to `VARCHAR(80)` (model + migration
  `0017_widen_worker_cycle_scopes`) so the folder id stays in the audit. Added a
  regression test that asserts the generated scope fits the column length
  (deterministic offline). Verified live: scoped job now → DONE with
  `market_scope = collection:market:folder=<uuid>` persisted. See
  [[feedback_sqlite_dialect_gotchas]].

## Tests
- `tests/test_watchlist_refresh_policy.py` (+2): `folder_id` scopes to a single
  folder without base union; scoped run respects the folder's type flag.
- `tests/test_api_collection_control.py` (+2): refresh enqueues a `refresh_all`
  job carrying `folder_id` + per-folder dedup_key; unknown folder → 404.

## Verification
- Offline: F3-relevant suites (watchlist policy, collection control API, worker
  jobs, ops scripts, system ops) PASS; ruff clean; frontend `npm run build` +
  `npm run lint` clean.
- Docker: api pytest (same set) + ruff PASS; `docker compose build web` PASS.

## Pre-existing unrelated failure (NOT this slice)
- `tests/test_api_control_room.py::test_control_room_promotes_live_overview_rails`
  fails on a clean tree (confirmed via `git stash`): it seeds market bars dated
  2026-05-30 and asserts `marketFreshnessStatus == "FRESH"`, but as the calendar
  advanced past the control-room staleness threshold the rail now reads STALE. A
  **date-drift time-bomb test** — needs its own cleanup slice (freeze "now" or seed
  relative dates). Independent of collection control.
