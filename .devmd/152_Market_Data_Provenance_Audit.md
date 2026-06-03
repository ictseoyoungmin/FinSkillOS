# 152 — Market Data Provenance Audit (Phase 2)

**Status:** Done.

"Why is the data in this state" — surfaces where the stored market bars came from,
so leftover synthetic (mock/test) rows are visible rather than silently rendered
as if real. Complements the same-day source dedup (101) + indicator backing-bar
guard (102) by making provenance auditable.

## Implemented
- **Repo** (`MarketRepository`): `source_distribution()` (bar counts per source) and
  `latest_source_by_ticker(timeframe)` (each ticker's newest bar source + time).
- **API** — `GET /api/system-ops/data-provenance` → `DataProvenanceReport`: source
  distribution (`synthetic` flag on mock/test), `totalBars` / `realBars` /
  `realRatioPercent`, `distinctTickers`, and `syntheticTickers` (tickers whose
  *newest* bar is synthetic — the actionable list) + a readable `detail`.
  `session is None` → db-unavailable shape.
- **Frontend** — a "Data Provenance" panel in System Ops → Worker Status (own
  query): "% real" badge, source distribution chips (synthetic ones outlined), and
  the synthetic-latest-bar tickers (hover = source + time).

## Tests
- `tests/test_api_system_ops.py`: seeded 3 yfinance + 1 mock bar → `totalBars=4`,
  `realBars=3`, `realRatioPercent=75`, source counts, `mock.synthetic=true`, and
  `syntheticTickers == {VIX}` (its newest bar is mock; SPY's is real).

## Verification
- Offline: system-ops + market-repo + v42 contract tests PASS; ruff clean; frontend
  build + lint clean.
- Docker: api pytest + ruff + build api/web.
- Live: current DB is 100% `yfinance` (mock junk previously cleaned) → reports all
  bars real, no synthetic tickers.

## Note
- "Real" = source not in {mock, test}; csv (operator-curated) counts as real. Next:
  Indicator/Bar Invariant Dashboard (153) — every indicator snapshot has a backing
  bar, etc. Data repair/quarantine (155) will act on what provenance/invariants
  surface (and will confirm scope before mutating).
