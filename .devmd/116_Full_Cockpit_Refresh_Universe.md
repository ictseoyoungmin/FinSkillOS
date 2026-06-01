# 116 — Full Cockpit Refresh Universe (no permanently-MISSING tabs)

Date: 2026-06-01

## Problem (spotted live)

The Analysis Workspace showed 10 sector / index ETFs (DIA, IWM, XLK, XLF, XLE,
XLV, XLI, XLY, XLP, XLU) permanently `MISSING`, even after a System Ops market
refresh. Root cause: the worker's refresh universe (12 tickers) was **narrower
than the Index Lab universe (17)** — the sector ETFs were never fetched, so no
amount of clicking "Refresh market data" could populate them.

(The user's question — "is there a dashboard control to turn on live collection?"
— is answered by the Slice-114 System Ops protocol buttons, which enqueue worker
jobs; this slice makes those jobs actually cover every tab.)

## Implemented

- `finskillos/data_sources/dto.py`: `DEFAULT_US_TICKER_UNIVERSE` broadened to the
  **union of every cockpit tab's tickers** (22): Analysis index + sector ETFs
  (SPY, QQQ, DIA, IWM, SMH, SOXX, XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU),
  Market Kernel / Symbol Lab mega-caps (NVDA, TSLA, AAPL, MSFT, AMZN), and the
  macro proxies (VIX, US10Y, DXY).
- `docker-compose.yml`: worker `FINSKILLOS_MARKET_REFRESH_TICKERS` /
  `FINSKILLOS_INDICATOR_REFRESH_TICKERS` defaults updated to the same 22-list.
- Local `.env` (gitignored) ticker lists updated to the 22-list — note: a present
  `.env` overrides the compose default, which is why the env, not just the code
  default, had to change.

## Tests

- `tests/test_market_data_service.py::test_default_universe_covers_analysis_index_universe`
  — asserts `DEFAULT_US_TICKER_UNIVERSE` is a superset of the Index Lab
  `DEFAULT_INDEX_UNIVERSE`, so the two can't drift back out of sync.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed.
- **Live**: recreated the worker → it auto-enqueued `refresh_all` and collected
  all 22 tickers via `yahoo`. The 10 sector ETFs now hold 251 real bars each, and
  `/api/analysis-workspace` reports `source=live, evidenceCoveragePercent=100,
  MISSING: none`. Done automatically through the request-driven queue.

## Known issues

- None. A present `.env` pins the universe; the committed code + compose default
  cover fresh clones.
