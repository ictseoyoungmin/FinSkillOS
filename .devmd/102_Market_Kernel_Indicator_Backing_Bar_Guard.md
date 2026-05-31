# 102 — Market Kernel Indicator Backing-Bar Guard

Date: 2026-05-31

## Problem (follow-up to 101)

After Slice 101 cleaned the mock *bars*, the Indicator Snapshot panel still led
the chart. `indicator_snapshots` carried the same mock-derived rows (computed
from the now-removed 00:00 UTC bars), and the route picked
`usable_indicators[-1]` purely by `snapshot_time`. So NVDA's panel showed the
orphaned 2026-05-31 00:00 snapshot (RSI 53.74 / EMA20 232.25 — a synthetic
Sunday) while the chart's last real bar was 2026-05-29 (RSI 46.30). 770
snapshots across 13 tickers were orphaned (no backing bar) by the mock delete.

## Implemented (code guard)

`api/routes/market_kernel.py`: the live read now only trusts an indicator
snapshot that has a backing (deduped) bar.

- Builds `bar_times` from the already-deduped `bars`.
- `backed_indicators` = usable snapshots whose `snapshot_time` is in
  `bar_times`; the latest of those is chosen.
- Falls back to the latest usable snapshot if none align (defensive, for edge
  tickers whose snapshot times legitimately differ from bar times).

This keeps the snapshot panel from ever leading the chart with a row left over
from removed/duplicated source data — the durable complement to the Slice-101
bar dedup.

## Tests added (`tests/test_api_market_kernel.py`)

- `test_market_kernel_indicator_ignores_snapshot_without_backing_bar` — seeds
  three real SPY bars + aligned snapshots plus one orphan snapshot on a later
  bar-less day with a distinct RSI; asserts the backed RSI wins (not the orphan)
  and the header latest still tracks the last real bar.

## Data cleanup (authorized, same mock effort)

`DELETE FROM indicator_snapshots` rows with no backing `market_bar` — 770 rows,
16399 → 15629, 0 orphans remaining. NVDA's latest snapshot reverts to
2026-05-29 04:00 (RSI 46.30 / EMA20 228.06), consistent with the chart. The
invariant "every indicator snapshot has a backing bar" is restored. (Other
consumers of `IndicatorRepository.latest_for`, e.g. Analysis / regime, also stop
seeing the phantom rows.)

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_market_kernel.py -q`
  ✅ (15 passed)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `ruff check` ✅ clean
- Docker pytest (kernel + v42 contract) ✅
- Live re-check: NVDA snapshot panel now RSI 46.30 / EMA20 228.06 (matches the
  clean yfinance chart, last bar 2026-05-29).

## Known issues

- None. Descriptive-only; no execution wording touched.
