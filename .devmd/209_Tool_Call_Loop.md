# 209 — Tool-Calling Loop (need → fetch → answer) (v3)

**Status:** Done. Gives the agent agency to pull data it's missing mid-turn: the
model requests reads, the backend fetches them, and the model answers — a single
bounded round. Most useful for capable models (Gemini); the deterministic
query-context (206/207) already covers the common cases.

## Implemented

### Chat (`finskillos/agent/chat.py`)
- System prompt: the model may reply with ONLY `{"need": ["events", "NVDA"]}`
  (targets: events / news / trades / any ticker) when it lacks data.
- `run_chat(..., fetch_more=...)`: after the first model reply, `_extract_need`
  detects a `need` block; if present (and a fetcher is supplied), `fetch_more` is
  called, the fetched data is appended to the wire (assistant request + system
  data + a "now answer" nudge), and the provider is called **once more** for the
  final answer. **Bounded to one round** (no recursion).

### Route (`api/routes/agent.py`)
- Supplies `fetch_more = lambda targets: build_query_context(session, " ".join(
  targets))`, so a requested read reuses the same query reader (events / news /
  trades / per-symbol) — no new fetch surface.

## Boundary
Read-only and descriptive; `fetch_more` only reads. The output guard still applies
to the final answer. No new write path.

## Tests (`tests/test_agent_chat.py` +2)
- two-turn stub: `{"need":["events"]}` → fetch → second call answers with the
  injected data (2 calls, data in the 2nd wire); a `need` block with no fetcher
  does not loop. Safety suite green.

## Verification
- Offline: chat + safety pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- Completes the three expansion candidates: 207 per-symbol detail, 208 multi-step
  chained actions, 209 tool-calling loop. The local 2B model won't reliably emit
  `need`; the deterministic context (206/207) is the reliable path, the loop adds
  agency for stronger models.
