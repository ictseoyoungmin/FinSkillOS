# 31 — Symbol Candles / Overlays / yfinance Adapter

Status: `DONE`
Date: `2026-05-25`

## Goal

Promote Symbol Lab chart evidence from a close-line table companion to a richer
technical chart surface:

- Render OHLC candles instead of a plain close line.
- Show volume bars under the candles.
- Support timeframe selection from Symbol Lab:
  `5m`, `15m`, `1h`, `1d`, `1w`, `1mon`, `1y`.
- Add selectable overlay indicators:
  EMA20, EMA60, EMA120, Bollinger bands.
- Replace direct Yahoo Chart HTTP parsing with the `yfinance` package.

## Boundary

Allowed:

- Keep DB storage canonical: `market_bars` already stores OHLCV rows.
- Convert provider output to `MarketBarDTO` at the adapter boundary.
- Add optional per-bar indicator fields to the Symbol Lab API response.
- Compute chart fallback overlays in React when historical indicator rows are
  not persisted.

Not allowed:

- Add execution/order/trade controls.
- Treat chart overlays as recommendations.
- Change the DB schema just to mirror provider-specific response shapes.

## Implementation Notes

The DB structure did not need a migration. `market_bars` already has:

```text
ticker, timeframe, bar_time, open, high, low, close, adj_close, volume, source
```

`yfinance.Ticker(symbol).history(...)` returns a tabular frame with columns
such as `Open`, `High`, `Low`, `Close`, `Adj Close`, and `Volume`. The adapter
normalizes those rows into `MarketBarDTO` before repository persistence.

`1y` is treated as a high-level Symbol Lab chart interval backed by yfinance
monthly history (`interval=1mo`) so it can be stored distinctly from daily
`1d` bars.

## Validation

Executed checks:

```bash
python3 -m ruff check api/routes/symbol_lab.py finskillos/data_sources/adapters/yfinance_adapter.py tests/test_market_data_service.py  # passed
timeout 60 python3 -m pytest tests/test_market_data_service.py tests/test_api_symbol_lab.py tests/test_api_v42_contract.py -q  # 36 passed
docker compose up -d --build api web  # passed; API image installed yfinance, web Vite build passed
curl -s 'http://localhost:8000/api/symbol-lab?ticker=TSLA&timeframe=1d'  # returned live Symbol Lab payload
docker exec finskillos-api python -c "import yfinance; print(yfinance.__version__)"  # 1.4.0
docker compose --profile e2e run --rm e2e npx playwright test e2e/visual --grep symbol-lab  # exit 0; 3 flaky retries passed
git diff --check  # passed
```

## Completion

- `requirements.txt` includes `yfinance`.
- `YahooChartMarketDataAdapter` now uses `yfinance.Ticker.history`.
- Symbol Lab accepts a `timeframe` query parameter.
- Symbol Lab renders candles, volume, and selectable overlay controls.
