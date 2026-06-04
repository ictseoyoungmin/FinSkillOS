# 158 — Portfolio Manual Entry / Edit (Phase 3)

**Status:** Done. First Phase-3 mutation slice — full descriptive holdings CRUD
+ snapshot baseline editing, wired into Mission Control. Builds directly on the
157 reconciliation read model (the editor updates the reconciliation line live).

Scope confirmed with the user: **Full CRUD (add / edit / delete position +
snapshot baseline) + edit-in-place + a "Clear sample" button.**

## Implemented

### API (idempotent, descriptive — no execution endpoints)
- `POST /api/mission-control/positions` — create a holding from `PositionInput`
  (ticker upper-cased; bootstraps the default account if none exists).
- `PUT /api/mission-control/positions/{id}` — full-field edit-in-place
  (404 `position_not_found` if the id is unknown).
- `DELETE /api/mission-control/positions/{id}` — remove one holding.
- `POST /api/mission-control/clear-positions` — remove every holding for the
  account (the "Clear sample" action).
- `PATCH /api/mission-control/snapshot` — partial-update the stored snapshot
  baseline (`totalValue` / `cashValue`; `None` leaves a field as-is, creating
  today's snapshot if none exists).
- Every mutation commits and returns the refreshed `_build_live_mission_control`
  snapshot, so `positions` + `reconciliation` come back current in one round-trip.
- All five return `503 db_unavailable` when no session is reachable (never a
  fixture — mutations must not silently no-op against sample data).
- Schemas: `PositionRow` (id + editable fields) now ships on
  `MissionControlResponse.positions`; `PositionInput`, `SnapshotBaselineInput`.
- Repos: `PositionRepository.update` / `.delete_all_for_account`,
  `PortfolioRepository.update_latest_baseline`.

### Frontend (Mission Control inline)
- `PortfolioEditorPanel` under the snapshot panel: holdings table with per-row
  Edit / Delete, an add/edit form (edit-in-place pre-fills + switches the submit
  to "Update position"), a snapshot-baseline editor, and a "Clear sample" button.
- `sendJson` client helper (POST/PUT/PATCH/DELETE) surfacing the API `detail`.
- Each mutation writes the returned snapshot straight into the
  `["mission-control"]` query cache, so the snapshot panel + reconciliation line
  update with no refetch.
- The whole editor is disabled (read-only notice) unless `source==="live"` and
  `db==="LIVE"` — fixture/offline shows the holdings but no controls.

## Tests
- `tests/test_api_mission_control.py` (+8): create (upper-cases ticker, appends),
  account bootstrap on first create, edit-in-place, 404 on unknown id, delete,
  clear-all, and snapshot-baseline PATCH driving reconciliation OK → MISMATCH.

## Verification
- Offline: mission-control + v42 contract + health + safety-language pytest PASS;
  ruff clean (backend + test).
- Frontend: `tsc -b` + `vite build` + eslint clean (one pre-existing
  ThemeProvider fast-refresh warning, unrelated).
- Docker: api pytest (mission-control + v42 + system-ops) + ruff + web build.

## Notes
- No migration (all columns already exist on `Position` / `PortfolioSnapshot`).
- No Playwright regen: the editor only renders controls in live mode; the forced
  `X-FSO-Use-Fixture` mission-control baseline is unchanged (fixture has no
  `positions`, so the editor shows the read-only notice there).
- Next: 159 Portfolio CSV Import / Export (reuse `PositionInput` for the row shape).
