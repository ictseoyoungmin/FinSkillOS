# 198 — Trades-Paste Ingestion (v3 Phase 11)

**Status:** Done. Extends the agent ingestion from portfolio holdings to **trade
journal** records — the second of the user's three inputs (portfolio · trades ·
watch). Same paste/screenshot → LLM-extract → preview → confirm flow.

## Implemented

### `finskillos/agent/ingest.py`
- `TradeRow` / `TradeIngestProposal` (normalized to the existing trade-import CSV
  columns) + `trades_from_records()` (LLM-extracted records → validated rows: ISO
  date or today, ticker, side normalized LONG/SHORT/WATCH/EXIT_REVIEW/OTHER/BUY/
  SELL from aliases) + `parse_trades_paste()` (deterministic fallback: header CSV
  or `TICKER SIDE [YYYY-MM-DD] [pnl]` lines).

### `finskillos/agent/chat.py`
- System prompt now documents **two** blocks: `{"holdings": [...]}` and
  `{"trades": [...]}`. `_extract_llm_action` parses whichever is present and
  builds a `ProposedAction` with `kind` (`portfolio_import` | `trades_import`) +
  `apply_endpoint`. Deterministic fallback tries holdings, then trades.

### API
- `ProposedActionVM.kind` is now a union + `apply_endpoint` is explicit. The chat
  response carries the right endpoint per kind.

### Frontend (`AgentChatWidget.tsx`)
- Preview/Confirm route by `action.kind`: portfolio → `previewImportPositions` /
  `applyImportPositions` (refreshes Mission Control); trades → `previewTradeImport`
  / `applyTradeImport` (`N valid / M invalid` → "Recorded N trade entries",
  invalidates the trade-memory query). Labels adapt (holdings vs trades).

## Boundary
Trades are still **preview → confirm** gated; the API import is append-only +
atomic + descriptive-wording-scanned (Slice 160). The agent only proposes.

## Tests (`tests/test_agent_chat.py` +2, `test_agent_ingest.py` +2)
- trades block → trades_import action + endpoint; deterministic trades fallback;
  `parse_trades_paste` positional/CSV; `trades_from_records` side normalization +
  bad-side warning.

## Verification
- Offline: chat + ingest + agent pytest PASS; ruff clean; tsc + eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Free-form quality scales with the model (Gemini ≫ 2B local); structured paste
  works offline via the deterministic parser. Next: 199 watchlist via chat.
