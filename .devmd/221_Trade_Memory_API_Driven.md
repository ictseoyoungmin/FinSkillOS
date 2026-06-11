# 221 — v4 Phase 14b: Trade Memory API-driven (remove manual entry form)

**Status:** Done. The frontend half of 14b — removes the manual entry **form/UI**,
makes the trade source API-driven (Toss sync + CSV/paste import). Backend was
already live-first (no auto-fixture for empty accounts — `_resolve_payload` returns
live-empty / live-error, fixture only on the explicit `X-FSO-Use-Fixture` opt-in).

## Implemented (`frontend/`)
- Deleted `TradeEntryForm.tsx` + `trade-entry-form.css` (manual entry form/UI).
- `TradeMemoryPage.tsx` — dropped the form + the `editEntry` edit flow (kept delete
  for cleanup). Added `TossTradeSyncPanel` (live only).
- `TossTradeSyncPanel.tsx` — "Sync trades" → `POST /api/agent/sync/trades/apply`
  (slice 220). Shows the result note (PENDING_TOSS until Toss enables CLOSED).
- `features/agent/{types,api}.ts` — `TradeSyncResponse` + `syncTossTrades()`.
- `RecentEntriesTable` now read+delete (no edit). `TradeCsvImport` (paste) kept as
  the interim manual-free input.
- e2e `news-events-memory.spec.ts` — replaced the form-store/side-selector specs
  with a "Toss sync panel present, form removed" spec; kept the API forbidden-wording
  test (the POST /entries API stays — only the UI form is removed).

## Verification
`tsc` + `vite build` + eslint clean (pre-existing warning only); Docker (rebuilt
web): build. CSS/JS shrank (form removed).

## Notes
- The backend `POST /api/trade-memory/entries` API is intentionally kept (used by
  the agent / safety test); only the manual UI form is removed.
- @visual baselines: Trade Memory layout changed → drift; user regenerates.
