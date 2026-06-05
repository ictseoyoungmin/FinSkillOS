# Phase 12 — Brokerage / Execution Boundary (deferred, optional)

Spec: [AGENT_INTERFACE_SPEC.md](AGENT_INTERFACE_SPEC.md) §Phase 12.

**Goal:** keep the architecture honest about where a brokerage API plugs in, and
reserve "execution" as a deliberate, separate, conservative decision — **last**,
**optional**, **off by default**. ("거래는 하지 않을 것이며 하더라도 가장 마지막에
보수적인 계약으로.")

## Scope

- **Read-only broker import (the only near-candidate, still deferred).** A
  `BrokerAdapter` that *imports* positions / trades from a brokerage API into the
  **same** Phase-9 `portfolio.import_positions` / `trades.import` tools. No new
  write power — just another source feeding descriptive bookkeeping.
- **Execution — out by default.** Not built without an explicit, separate
  decision. If ever:
  - **paper / simulation first**, behind an off-by-default capability flag;
  - a **separate confirmation contract**, distinct from bookkeeping confirms;
  - the rest of the cockpit stays descriptive — no buy/sell language leaks in;
  - its **own spec slice** precedes any code.

## Why it's here with no slices

This phase intentionally has **no near-term slices**. It documents the seam so
Phases 9–11 don't accidentally build toward execution, and so a future broker
integration is a *read adapter*, not a redesign. Execution remains a future,
conservative, opt-in contract the user decides on explicitly.

## Constraints

- The descriptive-only product boundary is never relaxed for the cockpit at large.
- Any execution capability is isolated, paper-first, off by default, and gated by
  its own contract — never reachable from the agent ingestion or narration paths.
