# Phase 16 — Market Data via Toss (v4)

**Goal:** Toss as a market-data source for KR + US symbols, supplementing the
existing yahoo/mock adapters used by System Ops refresh.

## Scope
- `finskillos/brokerage/toss/market.py` — map `GET /api/v1/candles` (OHLCV) →
  the market-bar shape the refresh pipeline ingests; `GET /api/v1/prices` →
  latest price; `GET /api/v1/stocks` → master (name/market/currency); `/warnings`
  → buy-warning flags. Register as a `FINSKILLOS_MARKET_REFRESH_ADAPTER=toss`
  option.
- Read-only; descriptive. No order/quote-to-trade conversion.

## Tests
Candle/price/stock fixtures → mapped bars/quotes; adapter selection. Offline.
