# 201 — Self-Review Polish (v3 Phase 11)

**Status:** Done. A review pass over the agent build (193–200) that fixed two real
bugs and polished the chat widget.

## Bugs fixed

### 1. Chat guard blocked legitimate trade-recording wording
After 197, `_CHAT_DIRECTIVE_PATTERNS` had `\b(buy|sell|short|long)\s+TICKER\b`,
which blocked the journaling agent's own descriptive replies — "Recorded your
**long TSLA**", "logged a **short NVDA** entry", "added your long TSLA and short
QQQ positions" — replacing them with the safe note. That broke the Slice-198
trades chat UX. Removed the bare ticker pattern; directives are still caught by
**imperative framing** ("should buy/sell/long/short", "buy now/it/today", "지금
매수하세요", "will rise", "guaranteed profit", "반드시 사세요"). Trade-recording
wording now passes; advice/predictions/guarantees still → safe note.

### 2. Watchlist deterministic parser false-fired on "watch"
`parse_watchlist_request` triggered on a bare `\bwatch\b`, so "watch out, the
market NVDA AAPL looks wild" proposed adding NVDA/AAPL. Tightened the keyword to
the compound watchlist term (`watchlist` / `관심종목` / `워치리스트`); loose phrasing
is still handled by the LLM block for capable models.

## Widget polish (`AgentChatWidget.tsx` + css)
- Markdown renderer now handles **numbered lists** (`1.`), **headings** (`#…`),
  and inline `` `code` `` (the local model uses these), still safely (no raw HTML).
- Provider picker closes on **outside click / Escape**.

## Tests (`test_agent_chat.py` +1, `test_agent_ingest.py` +1)
- trade-recording wording (long/short/bought TICKER) is allowed; "watch out …"
  does not false-fire. Safety-language acceptance suite still green.

## Verification
- Offline: chat + ingest + agent + safety + brokerage pytest PASS; ruff clean;
  tsc + vite build + eslint clean.
- Docker (rebuilt api + web): suites + web build.

## Notes
- Descriptive-only intact: the guard still blocks real advice/predictions/
  guarantees; it just no longer censors the agent's own descriptive bookkeeping.
