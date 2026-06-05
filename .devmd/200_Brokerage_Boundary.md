# 200 — Brokerage Read-Only Extension Boundary (v3 Phase 12)

**Status:** Done (boundary only — **no execution**). Keeps "추후 증권 API"
extensibility open while reserving execution as a separate, deferred decision.

## Implemented (`finskillos/brokerage/adapter.py`)
- `BrokerageReadAdapter` protocol — **read-only**: `available`, `fetch_positions`,
  `fetch_trades`, `snapshot`. **No order / execution method by design.**
- `BrokerageSnapshot` (positions / trades records) in the exact shape the Phase-11
  import accepts → a future broker feeds the *same* confirm-gated import
  (`proposal_from_records` / `trades_from_records` → preview → confirm). No new
  write power.
- `NullBrokerageAdapter` (default) + `build_brokerage_adapter()`
  (`FINSKILLOS_BROKERAGE_ADAPTER`; every value resolves to null — no real adapter
  ships). `EXECUTION_BOUNDARY` constant documents the contract.

## Tests (`tests/test_brokerage_boundary.py`, +5)
- default → empty null adapter; unknown name → null; **no execution attribute**
  (place_order/execute/buy/sell/trade); Null satisfies the read protocol; a broker
  snapshot flows into the existing import proposals.

## Boundary
Execution is **not implemented** and out of scope (user: "거래는 하지 않을 것이며
하더라도 가장 마지막에 보수적인 계약으로"). If ever added it is a separate,
conservative, paper-first, default-off, explicitly-authorized contract.

## Verification
- Offline: brokerage pytest PASS; ruff clean.
- Docker (rebuilt api): suites + ruff.

## Notes
- Closes the planned v3 Phase 7–12 arc: real-data integrity (7), layout (8), agent
  tool contract (9), LLM provider switching (10), agent ingestion — chat + paste +
  screenshot for portfolio/trades/watch (11), and the read-only brokerage boundary
  (12, no execution). docs/v3/PHASE_12 updated.
