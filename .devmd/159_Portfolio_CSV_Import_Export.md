# 159 — Portfolio CSV Import / Export (Phase 3)

**Status:** Done. Bulk holdings entry to complement the 158 manual editor.

Scope confirmed with the user: **upsert import (CSV tickers add/update, holdings
absent from the CSV are kept) with a dry-run preview → confirm**, mirroring the
155 data-repair safety pattern. Export is read-only.

## Implemented

### Service (`finskillos/services/portfolio_service.py`)
- `parse_portfolio_csv(text)` — string-based parser (extracted from
  `load_portfolio_csv`, which now delegates to it). Per-row numeric errors raise
  a `ValueError` naming the row + ticker so the API can surface it. Accepts the
  legacy `symbol` / `avg_price` aliases as before.
- `serialize_positions_csv(positions)` — renders holdings as
  `PORTFOLIO_CSV_COLUMNS` text; the same header the parser reads, so an export
  round-trips through import as pure UPDATEs.

### API (`api/routes/mission_control.py`)
- `GET /api/mission-control/positions/export.csv` — current holdings as a
  `text/csv` attachment (read-only; empty header-only body when no account).
- `POST /api/mission-control/import-positions` — dry-run **preview** by default
  (`adds` / `updates` / `totalRows` / per-row ADD|UPDATE tags, no mutation);
  `?confirm=true` upserts each row via `PortfolioService.upsert_position`,
  commits, and returns the refreshed Mission Control snapshot embedded in the
  result. A malformed CSV returns `status="ERROR"` with `parseErrors` and changes
  nothing. `503` when no DB session.
- Schemas: `PortfolioImportRequest` (`csvText`), `PortfolioImportRow`,
  `PortfolioImportResult` (`PortfolioImportResult.snapshot` is the live snapshot,
  populated only on APPLIED — declared after `MissionControlResponse` so the
  forward ref resolves under `from __future__ import annotations`).

### Frontend
- `PortfolioEditorPanel` gains an "Import / Export CSV" section: Export button
  (Blob download), CSV textarea + file picker, "Preview import" → shows
  `adds new · updates updated`, then an "Apply" button that upserts and writes the
  returned snapshot into the `["mission-control"]` query cache. Errors surfaced
  inline. Gated to live+LIVE like the rest of the editor.
- `sendJson`-based `previewImportPositions` / `applyImportPositions` +
  `downloadPositionsCsv` in `features/portfolio/api.ts`.

## Tests (`tests/test_api_mission_control.py`, +4)
- export round-trips (header + NVDA; re-import preview = pure UPDATE);
- dry-run computes adds/updates and does **not** mutate (positionCount stays 0);
- confirm upserts (existing ticker updated in place, new ticker added; snapshot
  returned with positionCount 2);
- malformed numeric cell → `status="ERROR"`, nothing applied.
- Existing `tests/integration/test_portfolio_import_flow.py` still green (the
  `load_portfolio_csv` refactor preserved its signature).

## Verification
- Offline: mission-control + v42 + health + safety-language + portfolio-import
  pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration. Upsert never deletes — the "replace-all" sync mode was offered
  and declined; if needed later it's a `?mode=replace` add-on.
- No Playwright regen (live-only controls; fixture path shows the read-only notice).
- Next: 160 Trade Import CSV (same dry-run→confirm shape, over the trade journal).
