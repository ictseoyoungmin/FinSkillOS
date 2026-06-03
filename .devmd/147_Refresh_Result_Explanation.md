# 147 — Refresh Result Explanation UX (Phase 1)

**Status:** Done.

The worker cycle audit showed per-component *status* (OK/NOOP) + scope, but not
*what was actually collected*. The rich counts already live in the cycle summary
JSONB — this surfaces them as counts + a human-readable outcome line so an operator
knows what the last refresh did (and why a tab is still partial).

## Implemented
- **API** — `WorkerCycleRecord` (in `workerStatus.recentCycles`) gains
  `barsWritten` / `articlesIngested` / `snapshotsWritten` / `failures` / `regime`
  (parsed from the cycle summary) and an `outcome` one-liner, e.g.
  "Collected 42 bars, 5 articles, 22 indicator snapshots, regime RISK_ON_OVERHEAT.
  1 ticker(s) failed and stay partial." A failed cycle reads "Cycle failed (Type) —
  no data was written; the next cycle retries." (`_worker_cycle_counts` +
  `_worker_cycle_outcome`).
- **Frontend** — Worker Status hero shows the latest cycle's outcome line; each
  Recent Cycle Trace row shows its outcome.

## Tests
- `tests/test_api_system_ops.py`: a cycle with a rich summary surfaces the counts +
  an outcome containing "42 bars", "regime RISK_ON_OVERHEAT", and "1 ticker(s)
  failed".

## Verification
- Offline: system-ops tests PASS; ruff clean; frontend build + lint clean.
- Docker: api pytest (system-ops + v42 contract) + build api/web.

## Note
- "Why a tab is stale/partial" is already on each tab's `dataState`
  (coverage/freshness, prior slices); this adds the worker-side "what the refresh
  did" half. Partial = per-ticker provider failures (counts here); auto-retry to
  reduce them is slice 148.
