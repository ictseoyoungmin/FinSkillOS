# 223 — v4 Phase 16: Toss Market-Data Adapter

**Status:** Done. Toss as a market source for the System Ops refresh, alongside
yahoo / mock.

- `toss/market.py` — `TossMarketDataAdapter(BaseMarketDataAdapter)`:
  `fetch_bars()` maps `GET /api/v1/candles` (OHLCV, 1d/1m) → `MarketBarDTO`,
  cursor pagination via `nextBefore` (bounded), range-filtered. `source="toss"`.
- `toss/client.py` — `candles(symbol, interval, count, before)`.
- `scripts/refresh_worker.py` — `FINSKILLOS_MARKET_REFRESH_ADAPTER=toss` resolves it.
- tests: candle→bar mapping, unsupported-timeframe raises, query params, worker
  resolution.
