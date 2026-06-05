# 190 — Agent Paste-Import UI (v3 Phase 11)

**Status:** Done. The user-facing half of ingestion: paste holdings → review the
parsed proposal → preview the import → confirm. The agent↔user interface the v3
brief described, for portfolio holdings.

## Implemented

### `features/agent/components/AgentIngestPanel.tsx`
A staged flow:
1. **Paste** — a textarea (with a format example) + "Parse paste".
2. **Review** — `POST /api/agent/ingest` (Slice 189) → a proposal table
   (ticker / qty / value / sector / theme) + a warnings list. Nothing written.
3. **Preview** — "Preview import" → `previewImportPositions(normalizedCsv)`
   (dry-run) → shows the add / update counts.
4. **Confirm** — "Confirm — N add / M update" → `applyImportPositions` →
   refreshes Mission Control via `onApplied`.

Reuses the existing audited portfolio import for every write; the `editable` gate
(live + DB LIVE) matches the editor, and writes are blocked otherwise with a note.

### Placement
- Rendered in Mission Control **beside** the portfolio editor — the
  `fso-mission-control-editor-row` is now a 2-column grid (editor `1.3fr` + paste
  `1fr`), collapsing to one column under 1100px. Uses the full-width row the
  Slice-183 layout opened up.

### Client
- `features/agent/api.ts::ingestPortfolioPaste` + `IngestProposalResponse` /
  `IngestRowVM` types.

## Boundary
Preview-only until confirm; descriptive bookkeeping (no orders/trades), surfaced
in the proposal `boundary`. Screenshot ingestion + trades-paste are later
enhancements on the same parse → preview → confirm flow.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web): web build.

## ⚠ Visual baselines
Mission Control gains the paste panel + the editor row becomes 2-col → its
`@visual` baseline drifts; the user regenerates.
