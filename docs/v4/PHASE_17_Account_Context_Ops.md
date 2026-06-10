# Phase 17 — Account Context + Read Tools + Ops Connect (v4)

**Goal:** surface Toss read data to the agent + an Ops connection panel.

## Scope
- Agent: `read.*` tools / state-context sections for accounts, buying-power,
  commissions, market-calendar (descriptive, read-only).
- Ops "Connect Toss" panel: connection status (token obtainable?), account pick
  (`accountSeq`), last sync time, a "Sync holdings now" button (Phase 14).
  Credentials are entered/stored server-side only (never returned to the client).

## Tests
Read-tool catalogue includes the Toss reads (still no execution tool); context
sections from fixtures; Ops status reflects configured/unconfigured. Offline.
