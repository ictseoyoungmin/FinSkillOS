# 98 — Market Kernel Multi-Timeframe

Date: 2026-05-30

## Goal

Second half of the "Market Kernel event overlay + multi-timeframe" item. The
Market Kernel page already had a 1D / 1W / 1M timeframe selector, but it was
**decorative**: `fetchMarketKernel` ignored it and the query key omitted it, so
clicking a timeframe did nothing. Wire it end to end.

## Implemented

- `api/routes/market_kernel.py`:
  - New `timeframe` query param (default `1d`). `_normalize_timeframe`
    (`SUPPORTED_MARKET_TIMEFRAMES = {1d, 1wk, 1mo}` + aliases like `1w`/`1m`;
    unsupported → `1d`).
  - The live read uses the resolved timeframe for bars + indicators, and
    `header.timeframe` reflects it (was hard-coded `DEFAULT_TIMEFRAME`).
  - Stays DB-read-only: a timeframe with no stored bars returns the explicit
    MISSING state (no provider call during render).
- Frontend:
  - `fetchMarketKernel(ticker, timeframe?, signal)` adds the `timeframe` query
    param.
  - `MarketKernelPage` maps the UI label (1D/1W/1M) → API code (1d/1wk/1mo),
    includes `timeframe` in the React Query key, and passes it to the fetcher —
    so the selector now refetches.

## Tests added

- `tests/test_api_market_kernel.py::test_market_kernel_reads_requested_timeframe`
  — stored 1wk bars are read for `?timeframe=1wk` (`header.timeframe="1wk"`,
  bars present); `?timeframe=1d` (no stored daily bars) is explicit MISSING;
  an unsupported timeframe normalises to `1d`.

## Notes

- Default timeframe is 1D and the `use_fixture` / forced-fixture path is
  unchanged, so the Market Kernel visual baseline is unaffected (no regen).
- Market Kernel is intentionally DB-read-only (unlike Symbol Lab's provider
  preview), so non-1d timeframes show MISSING until those bars are stored (e.g.
  via a System Ops / script refresh for that timeframe). The selector is now
  honest and functional rather than decorative.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_market_kernel.py -q`
  ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check api/routes/market_kernel.py tests/test_api_market_kernel.py`
  ✅ All checks passed
- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors
- `docker compose run --rm api python -m pytest tests/test_api_market_kernel.py
  tests/test_api_v42_contract.py -q` ✅ passed

## Known issues

- None. Completes the Market Kernel overlay + multi-timeframe item.
