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

## Implemented — Slice 200 (the boundary stub only)

`finskillos/brokerage/adapter.py`:
- `BrokerageReadAdapter` protocol — **read-only** (`available` / `fetch_positions`
  / `fetch_trades` / `snapshot`). **No order / execution method by design.**
- `BrokerageSnapshot` carries records in the exact shape `proposal_from_records`
  / `trades_from_records` accept, so a future broker feeds the same confirm-gated
  import — no new write power.
- `NullBrokerageAdapter` (default) + `build_brokerage_adapter()`
  (`FINSKILLOS_BROKERAGE_ADAPTER`, every value → null; no real adapter ships).
- `EXECUTION_BOUNDARY` constant states execution is out of scope — a separate,
  later, conservative, paper-first, default-off, explicitly-authorized decision.

Tests (`tests/test_brokerage_boundary.py`): default null + empty; unknown name →
null; **no execution attribute** (place_order/execute/buy/sell/trade); Null
satisfies the read protocol; a broker snapshot flows into the existing proposals.

Execution itself remains **not implemented** and out of scope.
