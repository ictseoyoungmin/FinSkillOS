# 199 — Watchlist via Chat (v3 Phase 11)

**Status:** Done. The third of the user's three agent inputs (portfolio · trades ·
**watch 폴더 추가/삭제**). "add NVDA to my watchlist" / "remove AAPL from watchlist"
→ a confirm-gated watch-folder update.

## Implemented

### `finskillos/agent/ingest.py`
- `WatchlistOp(add, remove, folder)` + `parse_watchlist_request()` (deterministic:
  requires a watch keyword — `watch`/`watchlist`/`관심종목`/`워치` — plus uppercase
  ticker tokens, with a small stoplist; `remove`/`삭제`/etc. → remove intent) +
  `watchlist_from_block()` (LLM `{"watchlist": [...] | {add, remove, folder}}`).

### `finskillos/agent/chat.py`
- System prompt documents a third block `{"watchlist": {add, remove, folder}}`.
  `_extract_llm_action` + the deterministic fallback build a `ProposedAction`
  `kind="watch_update"` carrying the `WatchlistOp` (folder defaults "Watchlist").

### API
- `ProposedActionVM.kind` adds `watch_update`; new `WatchlistOpVM` (add/remove/
  folder) on the proposed action.

### Frontend (`AgentChatWidget.tsx`)
- `watch_update` renders a direct **Apply to watchlist** button (no dry-run — the
  collection-control mutations are themselves reversible). On apply: fetch
  folders → find the target folder by name (case-insensitive) → create it if
  missing → `addFolderSymbol` / `removeFolderSymbol` per ticker → invalidate the
  collection-control query + report.

## Boundary
Still confirm-gated; reuses the existing collection-control endpoints (System
folder protections etc. intact). The agent only proposes.

## Tests (`tests/test_agent_chat.py` +1, `test_agent_ingest.py` +2)
- deterministic add/remove + keyword requirement; LLM block (list + object) →
  watch_update; folder/endpoint wiring.

## Verification
- Offline: chat + ingest + agent pytest PASS; ruff clean; tsc + eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Completes the agent ingestion triad (portfolio + trades + watch) via chat +
  paste + (vision) screenshot. Remaining: Phase 12 execution boundary (deferred).
