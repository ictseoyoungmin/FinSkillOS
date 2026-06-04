# 160 — Trade Import CSV (Phase 3)

**Status:** Done. The import counterpart to the existing trade-memory CSV export.

Trades are dated events with no upsert key, so import is **append-only** with the
same dry-run preview → confirm safety shape as 159, and is **atomic**: the confirm
path writes nothing unless every row is valid (descriptive-only wording included).

## Implemented

### Service (`finskillos/services/trade_journal_service.py`)
- `TRADE_CSV_COLUMNS` — the canonical column order, now the single source of
  truth shared with the export route (`_CSV_COLUMNS` re-imports it), so an export
  round-trips back through import as appended entries.
- `parse_trade_csv(text) -> list[TradeCsvRow]` — per-row validation (ISO
  `trade_date`, required ticker, allowed side via `_validate_side`, numeric
  cells, and the Slice-06 forbidden-wording scan via `_assert_entry_text_is_safe`).
  A failing row carries an `error` + `entry=None`; blank rows are skipped.

### API (`api/routes/trade_memory.py`)
- `POST /api/trade-memory/import` — dry-run **preview** by default (per-row
  OK/INVALID, `valid`/`invalid`/`totalRows`, error list, no write); `?confirm=true`
  bootstraps the default account if needed, `create_entry`s every row in one
  transaction, and commits. If any row is invalid → `status="ERROR"`, nothing
  written. Any write-time exception → atomic rollback + ERROR. No-session → ERROR
  (not persisted). Schemas `TradeImportRequest` / `TradeImportRow` /
  `TradeImportResult`.

### Frontend
- `TradeCsvImport` panel on Trade Memory (right column, under the entry form):
  file picker + CSV textarea, "Preview import" → per-row counts + flagged-row
  errors, then "Append N entries" (shown only when preview is all-valid). On
  APPLIED it invalidates `["trade-memory"]` so the page refetches. Gated to live.
- `previewTradeImport` / `applyTradeImport` (`sendJson`) + `tradeImport` endpoint.

## Tests (`tests/test_api_trade_memory.py`, +4)
- preview counts valid/invalid and does **not** mutate (recentEntries stays empty);
- confirm appends both rows (NVDA + AAPL visible);
- confirm with one invalid row → ERROR, atomic (nothing written);
- a row with forbidden wording in `notes` → flagged INVALID in preview.

## Verification
- Offline: trade-memory + mission-control + v42 + safety-language + portfolio
  import pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration. Append-only (no upsert) is the only sound semantics for an event
  log; export columns and import parser now share `TRADE_CSV_COLUMNS`.
- No Playwright regen (live-only controls; fixture path shows the read-only notice).
- Next: 161 Trade Memory Review Workflow Polish.
