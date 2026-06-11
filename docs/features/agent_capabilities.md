# Agent Capabilities

The cockpit ships a descriptive **analyst agent** (floating chat widget + backend).
It reads live state, queries the right data per question, and proposes
confirm-gated actions. It never places, modifies, or cancels orders — there is no
execution surface (enforced by tests).

## Chat + working-step streaming
- `POST /api/agent/chat` — single-shot reply.
- `POST /api/agent/chat/stream` — Server-Sent Events. Emits live **step** events
  (read portfolio → query each detected data source → generate) with
  running/done status + elapsed timers, then a final **reply** event. The widget
  renders the steps as the agent works.
- Providers: a local OpenAI-compatible LLM (default), Gemini (vision), or an echo
  fallback. Switchable in the Ops tab / widget. The descriptive-only output guard
  applies regardless of provider.

## Tool contract (`GET /api/agent/tools`)
A discoverable catalogue, each mapping to an existing endpoint. Categories:

- **read** — control room, risk firewall, market kernel, analysis workspace,
  events, news, trade memory, system status; Toss status / stock master /
  holdings warnings / market calendar / holdings P&L / prices; trade analytics
  (by-ticker / by-day / by-weekday / performance).
- **portfolio / trades / watch** — confirm-gated bookkeeping (import, edit,
  watchlist).
- **ops** — idempotent operational protocols: refresh market data / news /
  holdings news / events, recalculate indicators, recompute regime, run risk
  guards, and **sync portfolio / trades from Toss** (source of truth).
- There is **no** order / execute / buy / sell tool by design.

## Grounded answers
- Always-on **state context** (portfolio snapshot, regime, risk guards).
- Per-question **query context** — events / news / trades / per-symbol detail on
  intent, each fetched + (in streaming) timed as its own step.
- A bounded **tool-calling loop**: the model can request more data
  (`{"need":[…]}`), the system fetches it, and the model answers.

## Ingestion (confirm-gated)
Paste or screenshot holdings / trades / a watchlist → a structured, previewed
proposal the user confirms. USD values convert to KRW. Nothing is written until
confirmed.

## Holdings news (importance-ranked)
Per-holding news is ranked by an importance heuristic (classifier impact + risk +
sentiment + materiality keywords + recency, with near-duplicate de-dup); the LLM
re-ranks the shortlist into the final answer.

See also: [Toss integration](toss_integration.md) · [Trade analytics](trade_analytics.md).
