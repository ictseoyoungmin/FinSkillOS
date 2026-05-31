# 100 — Trade Memory Entry Edit / Delete / Export (UI)

Date: 2026-05-31

## Goal

Second half of the "Trade Memory edit/delete + export" item: surface the
Slice-99 backend seam in the cockpit. The Recent Entries table was read-only and
the journal form could only append.

## Implemented

- `frontend/src/features/trades/api.ts`:
  - `updateTradeEntry(id, input)` (PUT) and `deleteTradeEntry(id)` (DELETE),
    factored onto a shared `sendTradeEntry(method, url, input?)` that the
    existing `submitTradeEntry` (POST) now also uses.
  - `tradeMemoryCsvUrl()` → the export endpoint URL for a direct download link.
  - `endpoints.ts`: `tradeExport: "/trade-memory/export.csv"`.
- `RecentEntriesTable` — optional `onEdit` / `onDelete` / `busyId` props. When
  provided, renders an Actions column with Edit / Delete buttons (delete shows a
  "Removing…" busy state and is disabled while in flight).
- `TradeEntryForm` — optional `editEntry` / `onCancelEdit`. When set it prefills
  from the entry, switches the title/badge/submit copy to edit mode, and PUTs
  via `updateTradeEntry` instead of POSTing; saving or cancelling clears edit
  mode. `fromEntry` maps the VM back into form state.
- `TradeMemoryPage` — holds `editEntry` + `deletingId`; delete uses a
  `window.confirm` guard then invalidates the query; Edit loads the row into the
  form. Edit/Delete are offered only when `source === "live"` (mutating sample
  fixture rows makes no sense); the **Export entries (CSV)** link is always
  shown.
- CSS for the toolbar/export link and the row action / delete buttons.

## Notes

- Descriptive-only: no new copy introduces execution wording; the form keeps the
  Slice-12 side vocabulary and the write guard still gates edits server-side.
- Visual baseline: the trade-memory page now shows the Export link (and, in live
  mode, the Actions column), so the `trade-memory` screenshot baseline was
  regenerated. The structural contract test (required Evidence-to-Judgment
  panels) still passes unchanged; the full visual suite is green.

## Verification

- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors (pre-existing ThemeProvider fast-refresh warning
  only)
- `... playwright ... -g "trade-memory"` ✅ structural passes; visual baseline
  regenerated, then re-verified green
- `npm run test:visual` ✅ full visual suite green

## Known issues

- None. Completes the "Trade Memory edit/delete + export" queue item.
