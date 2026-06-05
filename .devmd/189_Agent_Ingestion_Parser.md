# 189 — Agent Ingestion Parser + Preview (v3 Phase 11)

**Status:** Done. Opens Phase 11 (the ingestion interface): free-form pasted
holdings → a structured, **not-yet-applied** proposal. Backend only; the paste UI
is the next slice.

## Implemented

### `finskillos/agent/ingest.py`
- `parse_portfolio_paste(text) -> IngestProposal` — deterministic + offline (no
  model call), so a paste always parses the same way. Handles:
  - **freeform** lines (`NVDA 10 ₩25,000,000 Semiconductors AI`) — ticker + numeric
    detection, currency symbols + thousands-commas stripped;
  - **comma / tab** rows;
  - a **header CSV** (column mapping: ticker / quantity / market_value / cost /
    sector / theme / strategy);
  - per-line **warnings** (no ticker, missing qty/value, duplicate ticker) — never
    crashes on a bad line.
- `IngestProposal.normalized_csv` emits exactly the columns the existing portfolio
  import accepts, so applying reuses the audited **dry-run → confirm** import path
  (no new mutation code).

### API
- `POST /api/agent/ingest` `{target:"portfolio", text}` → `IngestProposalResponse`
  (rowCount, rows, warnings, normalizedCsv, applyEndpoint, boundary). **No
  mutation** — preview only.

## Tricky bit
Comma is both a thousands separator and a CSV delimiter. The thousands-strip only
removes `digit , exactly-3-digits then non-digit/end`, so `₩25,000,000` collapses
while a CSV field comma like `5,1000000` is preserved.

## Tests (`tests/test_agent_ingest.py`, +8)
- freeform + currency/thousands; comma rows; header-CSV column mapping; duplicate
  + bad lines warn (no crash); empty → warning; normalized_csv has the import
  header; endpoint previews 2 rows with no mutation; endpoint reports warnings.

## Verification
- Offline: ingest + agent pytest PASS; ruff clean.
- Docker (rebuilt api): the same suites + ruff.

## Notes
- Next (190): the paste UI — textarea → parse → review table + warnings → apply via
  the existing import (dry-run → confirm). Screenshot ingestion (vision-capable
  providers) and trades-paste are later enhancements on the same flow.
