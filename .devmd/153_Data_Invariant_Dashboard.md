# 153 — Indicator / Bar Invariant Dashboard (Phase 2)

**Status:** Done. Read-only.

Slice 102 added a *read-time* guard so the Market Kernel never surfaces an
indicator snapshot without a backing bar. This makes that invariant **auditable**:
an operator can see whether any orphan snapshots exist (the phantom-indicator risk)
rather than relying on the read path to hide them.

## Implemented
- **Repo** (`IndicatorRepository`): `count_total`, `count_orphan_snapshots`, and
  `list_orphan_snapshots(limit)` — an indicator snapshot is an orphan when no
  `MarketBar` exists at the same `(ticker, timeframe, snapshot_time==bar_time)`
  (dialect-safe `NOT EXISTS`).
- **API** — `GET /api/system-ops/data-invariants` → `DataInvariantReport`:
  `status` (OK / VIOLATIONS / UNKNOWN), `totalSnapshots`, `orphanSnapshotCount`,
  `orphanSamples` (ticker / timeframe / at), and a readable `detail`. `session is
  None` → db-unavailable shape.
- **Frontend** — a "Data Invariants" panel in System Ops → Worker Status (own
  query): OK/VIOLATIONS badge, detail line, and orphan-ticker chips (hover =
  timeframe + time).

## Tests
- `tests/test_api_system_ops.py`: one snapshot with a backing bar + one without →
  `status=VIOLATIONS`, `totalSnapshots=2`, `orphanSnapshotCount=1`, sample ticker +
  date, detail mentions "phantom".

## Verification
- Offline: system-ops + v42 contract + signals tests PASS; ruff clean; frontend
  build + lint clean.
- Docker: api pytest + ruff + build api/web.

## Note
- These orphan snapshots are exactly what slice 102 cleaned by hand once; the
  **Data Repair / Quarantine** slice (155) will offer a safe protocol to remove
  them (and synthetic bars from 152) — that one mutates data, so its scope/policy
  is confirmed with the operator before building. Next read-only: 154 feed coverage.
