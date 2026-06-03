# 142 — Worker Failure-Recovery Docs (S7)

**Status:** Done. Docs-only (`docs/WORKER_QUEUE_AND_API_SPEC.md`).

Per the 2026-06-03 review (S7), documented the worker/job-queue failure and
recovery behavior that existed in code but wasn't written down, plus the regime
and folder-scope couplings added since the spec was last updated.

## Added / corrected
- **Cycle order + atomicity** — market → news → indicators → regime in one
  `session_scope()`; commit only at the end, so a mid-cycle exception rolls back
  (no partial writes). Corrected the old "nothing is written on failure" wording:
  an `ERROR` audit row *is* recorded.
- **Regime recompute (136)** — the cycle recomputes/persists the regime after
  indicators, gated `regime_enabled AND indicator_enabled`; summary `regime`
  section; Analysis Workspace `freshness=STALE` defense (137).
- **Folder-scoped refresh (134/F3)** — `payload.folder_id` collects only that
  folder's members; scope `collection:<type>:folder=<id>`.
- **Failure handling & recovery** — no automatic per-job retry (ERROR is terminal;
  recovery = next interval enqueue, since ERROR is not an *active* status, or a
  manual re-click); partial provider results don't fail the cycle (per-ticker
  failures are counts in the summary, cycle stays OK with PARTIAL coverage; only a
  structural failure raises). Verified against code:
  `JOB_STATUS_ACTIVE = (QUEUED, RUNNING)` and `MarketDataService.refresh_bars`
  never propagates (FAIL-AC-001).
- **Provider failure modes** — rate-limit / network / unsupported symbol / partial
  / holiday surface as counts + coverage state, not crashes; retry/backoff +
  circuit-breaking explicitly noted as **not yet implemented** (future work).
- `FINSKILLOS_WORKER_REGIME_ENABLED` added to the env table; change log updated
  (126–141 + this S7 update).

## Verification
- Doc claims cross-checked against `finskillos/db/models/system_ops.py`
  (`JOB_STATUS_ACTIVE`) and `finskillos/services/market_data_service.py`
  (non-propagating refresh). No code/test change.

## Follow-up (not this slice)
- Implement provider retry/backoff + per-provider circuit-breaking (the doc now
  marks this as a known gap).
