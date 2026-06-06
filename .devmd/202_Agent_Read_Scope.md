# 202 — Agent Read Scope (grounded chat + read tools) (v3)

**Status:** Done. Widens what the agent can *read* so it answers questions from
real state, and expands the tool catalogue with read tools. Descriptive-only.

## Implemented

### State context (`finskillos/agent/context.py`)
- `build_state_context(session)` → a compact descriptive snapshot: portfolio
  (total / cash / positions / largest %), market regime (+ mode / risk), risk-guard
  ladder status counts (+ overall), watchlist size, last trade date. Defensive —
  each read is independent; a missing piece is omitted, never an error;
  `session is None` → "".
- `run_chat(..., context=...)` injects it as a system message; `POST /api/agent/chat`
  reads it per turn (DB session). The agent now answers "what's my biggest
  position / regime / active guards?" from real data.

### Read tools (`api/agent_tools.py`)
- New `read` category over existing live read models: `read.control_room`,
  `read.risk_firewall`, `read.market_kernel`, `read.analysis_workspace`,
  `read.events`, `read.news`, `read.trade_memory`, `read.system_status` (all GET,
  non-mutating). Catalogue now 22 tools; still no execution tool.

### Spec
- `docs/v3/AGENT_INTERFACE_SPEC.md` — added the read-scope + screen-interpretation
  section.

## Boundary
The context is factual state labelled read-only; it must not become advice (the
output guard still applies to replies). Reads add no write power.

## Tests (`tests/test_agent_context.py` +3; `test_api_agent` category set updated)
- empty without a session; seeded snapshot is descriptive (no buy/sell/advice
  wording) with a clean weight %; context is grounded into the chat wire.

## Verification
- Offline: context + agent + chat pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- Next: 203 screen interpretation (capture the cockpit screen → vision provider).
