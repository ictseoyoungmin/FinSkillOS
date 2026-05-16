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
Status: TODO
Implemented data sources:
Implemented indicators:
Notes:
Known issues:
```
