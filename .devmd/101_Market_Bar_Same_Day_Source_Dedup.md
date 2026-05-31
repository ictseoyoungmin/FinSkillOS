# 101 — Market Bar Same-Day Source Dedup (read model)

Date: 2026-05-31

## Problem (spotted live, P1)

The Market Kernel NVDA chart rendered a violent sawtooth. Diagnosis from the
live DB:

- `market_bars` for `NVDA 1d` held 405 rows = 150 `mock` + 255 `yfinance`.
- The mock seed (2026-01-05..05-31, `bar_time` 00:00 UTC) overlapped the real
  yfinance data (2025-05-23..2026-05-29, `bar_time` 04:00 UTC). Same calendar
  day, different time-of-day → the unique key `(ticker, timeframe, bar_time)`
  does **not** treat them as duplicates.
- 101 NVDA days carried both sources at divergent closes (e.g. 2026-05-29 mock
  229.20 vs yfinance 211.14), and the chart plotted all 405 ordered by
  `bar_time`, so it zigzagged between the two series. The header's "latest"
  251.14 was a mock **weekend** bar (2026-05-31, a Sunday) past the real
  last trading day.
- Systemic: 13 `(ticker, 1d)` pairs are mixed (NVDA/QQQ/SMH/TSLA/US10Y/IONQ
  ~150 each; AAPL/SPY/MSFT/VIX/DXY/AMZN/SOXX 5–9 each). **Zero** mock-only
  pairs — every mixed pair is fully covered by yfinance.

## Implemented (this slice — code guard)

`finskillos/db/repositories/market_repo.py`:

- `_dedupe_period_bars(bars, timeframe)` — for daily-or-coarser timeframes,
  collapses bars sharing a calendar day to one, preferring a real source over
  `mock`, then the most recent `bar_time`. Intraday timeframes
  (`_INTRADAY_TIMEFRAMES`: 1m…4h) pass through untouched (several bars per day
  are legitimate there).
- `list_bars` applies the dedup after fetch and before the optional limit, so
  the chart series — and every `len(bars)`-derived coverage number in
  `api/routes/market_kernel.py` — is one point per day.
- `latest_bar` / `latest_bar_time` are intentionally left raw: the incremental
  refresh policy needs the true stored max `bar_time`, not the deduped view.

This tolerates legacy mixed-source rows with no migration and prevents the
sawtooth from recurring if mixed sources are ingested again.

## Tests added (`tests/test_market_repo_dedup.py`)

- same-day mock+yfinance collision → one bar, the yfinance close wins;
- a day with only a mock bar is retained (no coverage loss);
- intraday (1h) keeps every same-day bar.

## Data cleanup (authorized, separate from this commit)

User authorized deleting the superseded mock seed. Because mock-only pairs = 0,
`DELETE FROM market_bars WHERE source='mock'` (941 rows) removes the seed with
no coverage loss; every remaining day is real yfinance data and the header's
latest reverts to the real last trading day. Recorded in CURRENT_STATE.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_market_repo_dedup.py
  tests/test_market_data_service.py tests/test_api_market_kernel.py -q` ✅
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `ruff check` ✅ clean
- Docker pytest (market repo + kernel + v42 contract) ✅
- Live chart re-checked after the mock cleanup (single clean yfinance series).

## Known issues

- None. Descriptive-only; no execution wording touched.
