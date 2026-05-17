# 04 — Market Data and Signals

## Goal

Implement market data ingestion, storage, and signal calculation for core indices, ETFs, and symbols.

## Scope

Market data should support:

```text
- Index Lab
- Symbol Lab
- Market Regime
- Portfolio Risk
- Event Radar
```

## Initial ticker universe

```text
Core market:
SPY, QQQ, VIX proxy/index if source supports it, DXY proxy, TNX proxy

Sector/theme:
SMH, ARKX, SRVR, PAVE

Symbols:
TSLA, NVDA, RKLB, ASTS, PLTR, AAPL, MSFT, AMZN
```

Use configurable watchlists, not hardcoded-only lists.

## Data model

Use `market_bars` with:

```text
ticker
timeframe: 1h / 1d / 1wk / 1mo
bar_time
open
high
low
close
adj_close
volume
source
```

## Indicator snapshots

Calculate at minimum:

```text
rsi_14
ema_20
ema_60
ema_120
bb_mid
bb_upper
bb_lower
volume_zscore
momentum_score
trend_state
```

## Services and modules

```text
finskillos/services/market_data_service.py
finskillos/services/signal_service.py
finskillos/signals/technical.py
finskillos/db/repositories/market_repo.py
finskillos/db/repositories/indicator_repo.py
```

## Optimization requirements

- Use incremental update by ticker/timeframe.
- Do not download full history on every app refresh.
- Cache raw responses.
- Store indicator snapshots.
- UI reads snapshot data first.

## Acceptance criteria

- Historical daily data can be stored for a ticker.
- RSI/EMA/Bollinger values are calculated and persisted.
- Duplicate bars are not inserted.
- Signal calculation can run for at least 20 tickers within a reasonable local time budget.
- Failure to fetch one ticker does not crash the app.

## Test commands

```bash
pytest tests/test_market_data_service.py tests/test_signals.py -q
```

## Completion placeholder

```text
Status: DONE (2026-05-17)

Implemented data sources:
- finskillos/data_sources/dto.py                 (MarketBarDTO, IndicatorSnapshotDTO, DEFAULT_TIMEFRAME, DEFAULT_US_TICKER_UNIVERSE = SPY/QQQ/NVDA/TSLA/AAPL/MSFT/AMZN/SMH/SOXX/VIX/US10Y/DXY)
- finskillos/data_sources/market_adapter.py      (BaseMarketDataAdapter abstract; MockMarketDataAdapter — deterministic sin+drift per ticker; CsvMarketDataAdapter for the sample fixture; MarketDataFetchError for soft per-ticker failure)
- finskillos/data_sources/__init__.py            (re-exports the adapter surface so callers import from a single module)

Implemented indicators:
- finskillos/signals/technical.py                (pure-Python SMA, EMA, RSI (Wilder), Bollinger 20/2σ, volume_zscore, momentum_score, trend_state; index-aligned outputs, Decimal-typed results, no pandas/numpy dependency)

Implemented persistence:
- finskillos/db/models/market.py                 (MarketBar ORM; unique (ticker, timeframe, bar_time); idx_market_bars_lookup)
- finskillos/db/models/indicator.py              (IndicatorSnapshot ORM; unique (ticker, timeframe, snapshot_time); idx_indicators_lookup)
- finskillos/db/migrations/versions/0002_market_data_foundation.py (upgrade adds market_bars + indicator_snapshots tables and indexes; downgrade drops them)
- finskillos/db/repositories/market_repo.py      (MarketRepository: upsert_bar/upsert_bars, list_bars, latest_bar/latest_bar_time/latest_close, count_for)
- finskillos/db/repositories/indicator_repo.py   (IndicatorRepository: upsert_snapshot/upsert_snapshots, latest_for, list_for)

Implemented services:
- finskillos/services/market_data_service.py     (MarketDataService.refresh_bars uses adapter.start = latest stored bar_time; drops duplicates so re-runs only append; returns MarketRefreshReport with per-ticker TickerRefreshResult; FAIL-AC-001 isolates per-ticker failures; import_bars bypasses adapter for CSV/manual loads; get_bars/get_latest_price feed Mission Control)
- finskillos/services/signal_service.py          (SignalService.compute_indicators reads bars, runs all six indicator families + trend_state, upserts the latest snapshot by default; persist_history=True backfills; MIN_BARS_FOR_INDICATORS=15 prevents partial RSI; get_latest_indicators returns descriptive payload only)

Tests added:
- tests/fixtures/market_bars/sample_daily_bars.csv (SPY + TSLA, 10 daily bars each, hand-authored OHLCV)
- tests/test_market_data_service.py              (11 tests: deterministic mock adapter, mock failing-tickers, CSV adapter happy/missing-ticker, refresh writes initial history, DATA-AC-002 incremental refresh, FAIL-AC-001 per-ticker isolation, get_latest_price, default US universe assertion, import_bars upsert idempotency)
- tests/test_signals.py                          (15 tests: SMA/EMA alignment, RSI canonical series ≈ 70.464, RSI monotone → 100, Bollinger formula + 2σ width, volume z-score zero/spike, momentum percent change, trend_state descriptive labels only — no BUY/SELL/매수/매도 — period validation, service writes latest snapshot, service backfills full history, insufficient-history skip, IndicatorRepository upsert idempotency, get_latest_indicators emits descriptive payload only — SAFE-AC-001)

Notes:
- Market outputs are descriptive only: indicators + trend_state labels (BULLISH / WEAK_BULLISH / NEUTRAL / WEAK_BEARISH / BEARISH). No buy/sell text is generated anywhere in this slice — verified by an explicit SAFE-AC-001 string check in tests/test_signals.py.
- Default ticker universe is US-market focused per the slice prompt: SPY, QQQ, NVDA, TSLA, AAPL, MSFT, AMZN, SMH, SOXX, VIX, US10Y, DXY (configurable via the MarketDataService constructor).
- Live providers (yfinance, Polygon, Alpha Vantage) are intentionally NOT wired up. MockMarketDataAdapter + CsvMarketDataAdapter give the rest of the stack deterministic offline data so tests run without an internet connection (docs/v2_1/09 §4 deterministic-test requirement).
- DB layer relies on the cross-dialect SQLAlchemy types only (Uuid, Numeric, DateTime(timezone=True), String). No PostgreSQL-specific features were introduced in slice 04, so the existing alembic SQLite smoke continues to work and a dedicated PostgreSQL smoke remains deferred until a future slice introduces JSONB/array columns.
- Incremental policy follows docs/v2_1/08 §5.5: MarketRepository.latest_bar_time seeds the adapter `start` parameter and a defensive `_as_utc` normalisation handles SQLite returning naive datetimes.

Verification:
- python3 -m compileall app.py finskillos scripts                                              ✅ no errors
- python3 -m pytest tests/test_market_data_service.py tests/test_signals.py -q                 ✅ 26 passed
- python3 -m pytest tests -q                                                                    ✅ 87 passed (slice 02 + slice 03 + slice 03 cleanup + slice 04)
- python3 -m ruff check  (every slice-04 + cleanup file)                                        ✅ All checks passed

Known issues:
- No live market-data adapter (yfinance / Polygon / Alpha Vantage) is implemented. When ready, the only work is adding a new class that emits MarketBarDTO — the service / repository / indicator layers do not need to change.
- Streamlit Market Kernel / Index Lab / Symbol Lab UIs are intentionally deferred per the slice prompt.
- A PostgreSQL smoke run is deferred because slice 04 introduced no PostgreSQL-specific column types. The existing SQLite migration smoke covers market_bars + indicator_snapshots schema creation.
- Regime Engine, Risk Guards, News Intelligence, Event Radar, and direct buy/sell recommendations are out of scope for slice 04 and remain to be implemented in their own slices.
```
