# 148 — Provider Failure / Retry / Backoff (Phase 1)

**Status:** Done. Implements the gap S7 (slice 142) documented.

Real-data (yahoo/yfinance) is the default adapter, so transient provider errors
(rate-limit / network / partial) directly reduce coverage. Previously a single
fetch failure recorded the ticker failed immediately; now a transient error gets a
bounded retry before giving up.

## Implemented
- **`MarketDataService`** gains `fetch_retries` / `fetch_backoff_seconds` / `sleep`.
  `_fetch_with_retry` retries **only** the declared transient
  `MarketDataFetchError` up to the budget, with exponential backoff
  (`backoff * 2**attempt`); unexpected exceptions are not retried (fail fast to the
  existing generic handler). `fetch_retries=0` → single attempt, identical to before.
  `sleep` is injectable so tests don't actually wait.
- **Worker** reads `FINSKILLOS_MARKET_FETCH_RETRIES` (default 2 → up to 3 attempts)
  and `FINSKILLOS_MARKET_FETCH_BACKOFF_SECONDS` (default 1.0) and passes them to the
  market service. Keys added to the runtime allow-list + `.env.example`.
- Worker spec updated (`WORKER_QUEUE_AND_API_SPEC.md`): retry/backoff is no longer a
  gap; whole-cycle/job auto-retry + circuit-breaking remain future work.

## Tests (offline, no real sleep)
- `tests/test_market_data_service.py`: a flaky adapter failing twice then
  succeeding → retried within budget, 1 bar written, no failures; a permanently
  failing adapter → 3 attempts then recorded failed, and the injected `sleep`
  received the exponential delays `[0.5, 1.0]`.

## Verification
- Offline: market-data + ops-scripts + worker-jobs + system-ops + config tests
  PASS; ruff clean.
- Docker: api pytest (same set) + ruff PASS.

## Note
- Retry is **per-ticker fetch** (transient). A failed *cycle/job* still has no
  auto-retry — that's the next-cadence path + the Slice-146 Retry button. Indicator
  computation reads stored bars (no provider), so it needs no retry.
