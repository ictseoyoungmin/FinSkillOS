# 214 — v4 Phase 14 (backend): Toss Holdings Sync

**Status:** Done (backend). Reads the user's real Toss holdings into a
confirm-gated portfolio-import proposal — the API replacement for the manual
paste. Frontend "Sync from Toss" button is slice 215.

## Implemented
- `finskillos/agent/ingest.py` — `_SYMBOL_RE` accepts KR 6-digit codes (e.g.
  005930) on the **structured** records path (`proposal_from_records`) so Toss KR
  holdings aren't dropped; the loose positional text parser stays strict
  (`_TICKER_RE`).
- `finskillos/brokerage/toss/adapter.py` — `TossBrokerageAdapter`
  (`BrokerageReadAdapter`): `fetch_positions()` maps `/api/v1/holdings` items →
  `{ticker, quantity, market_value(=marketValue.amount), average_cost(=
  averagePurchasePrice), currency, name}`. `fetch_trades()` → `[]` (Phase 14b).
  No execution method.
- `finskillos/brokerage/adapter.py` — `build_brokerage_adapter("toss")` resolves
  the Toss adapter; default stays `NullBrokerageAdapter`.
- `POST /api/agent/sync/holdings` (`api/routes/agent.py`) → `BrokerageSyncResponse`:
  unavailable note when Toss unconfigured; else `proposal_from_records(records,
  usd_krw_rate=…)` (USD→KRW, slice 210) → rows + normalized_csv + applyEndpoint.
  Read failure surfaces as a warning, never a 500.

## Tests (+ )
- `test_toss_adapter.py` (4): KR+US mapping, unavailable, no trade/exec method,
  KR symbol survives `proposal_from_records` + USD→KRW.
- `test_api_agent_sync.py` (3): unconfigured → available=false; stub adapter →
  proposal with KR symbol + USD conversion + applyEndpoint; read-failure warning.

## Verification
Offline pytest + ruff; Docker (rebuilt api): toss/adapter/sync/ingest/boundary/v42
+ ruff — all green.

## Boundary
Read + confirm-gated import; no order placement. Apply reuses
`/api/mission-control/import-positions` (dry-run → confirm) + baseline reconcile
(slice 211, in the widget).

## Next
215 — frontend "Sync from Toss" button → preview → confirm.
