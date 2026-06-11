# 217 — v4: Toss Replace-Sync Service (holdings + cash, source of truth)

**Status:** Done (service + manual apply endpoint). The auto/replace counterpart
to the confirm-gated button (215): the broker is the single source of truth, so a
sync **replaces** the recorded portfolio (stale tickers removed) and sets real
cash. Worker daily auto-gate is slice 218.

## Implemented
- `finskillos/brokerage/toss/client.py` — `buying_power(currency)`.
- `finskillos/brokerage/toss/adapter.py` — `fetch_cash(rate)` → KRW cash
  (buying-power KRW + USD→KRW). None on failure → caller keeps existing cash.
- `finskillos/services/brokerage_sync_service.py` — `sync_toss_portfolio(session)`:
  holdings → records → USD→KRW proposal → **delete_all_for_account + upsert**
  (replace) → snapshot baseline = positions + cash. Skips when unconfigured.
- `POST /api/agent/sync/holdings/apply` — runs it, no confirm (read-only broker
  side; the user opted into source-of-truth overwrite). Surfaces failure as a
  warning, never 500.

## Tests
- `test_toss_adapter.py` (+1): fetch_cash combines KRW + USD→KRW.
- `test_api_agent_sync.py` (+2): unconfigured skip; apply REPLACES (a seeded OLD
  ticker is gone after a second sync) + cash set, over a live sqlite DB.

## Verification
Offline pytest (76) + ruff; Docker (rebuilt api): sync/adapter/client/boundary/v42/
mission-control + ruff — green.

## Boundary
Broker read-only; this writes only the bookkeeping DB (positions + baseline).
No order placement. Fixes the stale-duplicate + stale-cash issue the user saw.

## Next
218 — worker runs this once a day automatically (+ worker env passthrough).
