# 220 — v4 Phase 14b: Toss Trade Sync (executed orders → journal)

**Status:** Done (backend). Imports executed Toss orders into the trade journal,
idempotently. Built per plan against `status=CLOSED`; reports PENDING_TOSS while
Toss's live `closed-not-supported` gate is in effect (verified live: 400). Frontend
cleanup is slice 221.

## Implemented
- `toss/adapter.py` — `fetch_trades()` paginates `orders(status=CLOSED)` →
  `_order_to_trade_record` (skips unfilled). Propagates `TossApiError`.
- `services/brokerage_sync_service.py` — `sync_toss_trades(session)`: dedup by
  `event_key="toss:{orderId}"`, USD→KRW, creates `TradeJournalInput` entries.
  Returns SKIPPED / PENDING_TOSS (closed-not-supported) / APPLIED{added,skipped}.
- `POST /api/agent/sync/trades/apply` (`TradeSyncResponse`).
- `scripts/refresh_worker.py` — daily cycle also runs the trade sync (logged,
  independent of the portfolio sync; PENDING_TOSS until Toss enables CLOSED).

## Why /api/v1/trades is NOT used
That endpoint is the market-wide anonymous tape (no account header, no side / my
quantity / orderId / history; today's ≤50 ticks). Personal executed history is
account-scoped CLOSED orders only.

## Tests
adapter mapping + CLOSED-error propagation; service PENDING_TOSS / unconfigured /
APPLIED + idempotent dedup; endpoint PENDING_TOSS + APPLIED. Offline.

## Verification
Offline pytest + ruff; Docker (rebuilt api/worker): trade-sync/adapter/worker/
trade-memory/v42/boundary + ruff — green. Live: CLOSED → 400 closed-not-supported
(confirmed), so sync reports PENDING_TOSS today.

## Next
221 — frontend Trade Memory: remove fixture fallback + manual entry form, API-driven.
