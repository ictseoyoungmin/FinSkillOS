# 111 — Real-Data Market Refresh Default (kill the mock sawtooth)

Date: 2026-06-01

## Problem (P0, spotted live)

The Market Kernel NVDA chart sawtoothed again (301 deduped bars). Root cause: the
market-refresh **default adapter was `mock`** in both the worker
(`scripts/refresh_worker.py`) and the System Ops `refresh-market-data` route, so
any refresh re-seeded synthetic `mock` bars. `MockMarketDataAdapter` emits a bar
for *every* calendar day (incl. non-trading days yfinance never covers) at a
different price level (~229) than the real yfinance series (~211). The Slice-101
read-model dedup collapses **same-day** source collisions but cannot drop a mock
bar on a day yfinance simply has no bar — so those mock-only days interleave with
real days and sawtooth. (1911 mock bars had accumulated across refreshes.)

## Implemented

- Default the market-refresh adapter to **`yahoo`** (real data); `mock` is now
  explicit opt-in only:
  - `scripts/refresh_worker.py` `load_config` default `mock → yahoo`.
  - `api/routes/system_ops.py` `_invoke_market_refresh` default `mock → yahoo`.
  - `docker-compose.yml` worker `FINSKILLOS_MARKET_REFRESH_ADAPTER` default
    `:-mock → :-yahoo`.
  A failed real fetch (offline) writes nothing — it never falls back to mock, so
  no synthetic junk is introduced.
- `tests/conftest.py`: new **autouse** `_offline_market_adapter` fixture forces
  `FINSKILLOS_MARKET_REFRESH_ADAPTER=mock` for every test (and `clean_env`
  re-sets it after its strip loop), so the suite stays offline regardless of the
  production default; a test that needs another value still overrides via its own
  `monkeypatch.setenv`.

## Data cleanup (authorized)

Re-cleaned the re-seeded junk from the live DB (mock-only `(ticker,timeframe)`
pairs = 0, so coverage-safe):
- `DELETE FROM market_bars WHERE source='mock'` — 1911 rows.
- `DELETE` orphaned `indicator_snapshots` (no backing bar) — 103 rows.
NVDA 1d reverts to 255 yfinance bars (2025-05-23..2026-05-29), latest close
211.14, real indicators. Live chart re-checked: single clean series.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed (offline).
- `ruff check` ✅ clean.
- Docker pytest (system_ops + operations_scripts + v42 contract) ✅ — confirms
  tests stay offline even with postgres reachable.
- api rebuilt + recreated (yahoo default); live `/api/market-kernel?ticker=NVDA`
  → barCount 255, latest 211.14 @ 2026-05-29, no sawtooth.

## Known issues

- Worker still only auto-runs behind the `worker` compose profile (Slice 112)
  and has no request queue yet (Slice 113); this slice only stops the junk
  source and re-cleans.
