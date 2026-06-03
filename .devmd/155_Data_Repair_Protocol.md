# 155 — Data Repair Protocol (Phase 2) — closes Phase 2

**Status:** Done. **Data-mutating** — scope + policy confirmed with the operator
before building.

Turns the manual cleanups of slices 101/102 (synthetic mock bars + orphan
indicator snapshots) into a safe System Ops protocol. Operator-confirmed policy:
**target both** (synthetic bars + orphan snapshots) with **dry-run → confirm
hard-delete**.

## Implemented
- **Repos**:
  - `MarketRepository.{count_bars_by_sources, tickers_by_sources,
    delete_bars_by_sources}` — count / list-tickers / hard-delete by source.
  - `IndicatorRepository.delete_orphan_snapshots` — delete snapshots with no
    backing bar (PK-subquery IN delete, SQLite+Postgres safe).
- **API** — `POST /api/system-ops/data-repair` → `DataRepairResult`. **Dry-run by
  default**: reports `syntheticBarCount` + `syntheticTickers` + `orphanSnapshotCount`,
  deletes nothing. `?confirm=true`: deletes synthetic (mock/test) bars then orphan
  snapshots (recomputed, so it also clears snapshots orphaned by the bar deletion),
  returns the deleted counts, logs the action. **Real (yfinance/csv) bars are never
  deleted.** `session is None` → db-unavailable shape.
- **Frontend** — a "Data Repair" panel in System Ops → Worker Status: "Preview
  cleanup (dry-run)" → shows what would be removed → an explicit
  "Delete N bars + M snapshots" confirm button → applies + refreshes the
  provenance/invariant panels. Backup reminder in the copy.

## Tests
- `tests/test_api_system_ops.py`: seeded 1 real + 2 mock bars + 1 orphan snapshot.
  Dry-run reports 2 synthetic (VIX) + 1 orphan, deletes nothing; confirm deletes
  2 bars + 1 snapshot, the real SPY bar survives, orphan count → 0.

## Verification
- Offline: system-ops + market-repo + v42 contract tests PASS; ruff clean; frontend
  build + lint clean.
- Docker: api pytest + ruff + build api/web.
- Live: DB is clean (0 synthetic, 0 orphan) → dry-run reports "nothing to repair";
  no deletion performed.

## Phase 2 complete (151–155)
Provider health · provenance · invariants · feed coverage · data repair. The
"data trust / provider resilience" surface is in place. Next per ROADMAP: Phase 3
(portfolio / journal real-use input).

## Follow-up (noted)
- Audit the confirmed repair into a durable System Ops history row (today it logs +
  returns the result). Would need a protocol-key/audit shape; deferred.
