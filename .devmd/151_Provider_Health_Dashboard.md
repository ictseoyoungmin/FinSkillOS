# 151 — Provider Health Dashboard (Phase 2)

**Status:** Done. Opens Phase 2 (data trust / provider resilience).

Real-data (yahoo) is the default and 148 added retry/backoff, so the operator now
needs to see *provider-level* health — last success, last failure, why, and which
tickers — not just per-cycle counts.

## Implemented
- **Worker** — the market cycle summary now records `failedTickers`
  (`[{ticker, error}]`, capped at 15) so the failure detail is persisted, not just
  a count.
- **API** — `workerStatus.providerHealth` rolled up from the recent (25) cycle
  audit: `adapter`, `status` (HEALTHY / DEGRADED / FAILING / UNKNOWN),
  `lastCycleAt`, `lastSuccessAt` (last fully-clean cycle), `lastFailureAt`,
  `consecutiveFailureCycles`, `affectedTickers` (from the most recent cycle with
  failures), and a readable `detail`. DEGRADED = latest cycle wrote some bars but
  some tickers failed; FAILING = recent cycles collected nothing.
- **Frontend** — a "Provider Health" panel in System Ops → Worker Status:
  status-toned badge + detail line, last-clean / last-failure (relative time) /
  failing-cycle count, and the affected-ticker chips (hover shows the error).

## Tests
- `tests/test_api_system_ops.py`: two seeded cycles (older clean, newer partial)
  roll up to `DEGRADED`, `consecutiveFailureCycles=1`, lastSuccess=older,
  lastFailure=newer, affected = {VIX, US10Y}.

## Verification
- Offline: system-ops + ops-scripts tests PASS; ruff clean; frontend build + lint
  clean.
- Docker: api pytest (system-ops + ops + v42 contract) + build api/web.

## Note
- Computed from the existing cycle audit (no new table). Indicators read stored
  bars (no provider), so provider health is market-focused; news (RSS) coverage is
  the separate Phase-2 "feed coverage diagnostics" slice. Next: Market Data
  Provenance Audit.
