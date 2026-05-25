# 22 — Market Provider Adapter

Status: `DONE`
Date: `2026-05-25`

## Goal

Add the first external market-data provider adapter without changing product
tab source semantics.

This slice makes live ticker/bar collection possible through the manual
refresh command:

```bash
python3 scripts/refresh_market_data.py --adapter yahoo --tickers SPY QQQ TSLA
```

The React cockpit tabs remain fixture-first until their DB-backed read models
are promoted separately.

## Boundary

Allowed:

- Fetch OHLCV bars from Yahoo Chart API via an explicit CLI opt-in.
- Normalize provider payloads into `MarketBarDTO`.
- Persist bars through the existing `MarketDataService`.
- Keep per-ticker failures isolated.

Not allowed:

- Fetch live market data during API page rendering.
- Add trading/execution endpoints.
- Pretend news data is live provider-backed.
- Make visual baselines depend on internet access.

## News / Ticker Status

Ticker market bars can now be fetched through the `yahoo` adapter when the
host has internet access. News remains manual/sample only; live news provider
selection, rate-limit policy, and attribution rules are deferred.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_market_data_service.py tests/test_operations_scripts.py -q
python3 -m ruff check finskillos/data_sources/adapters/yfinance_adapter.py finskillos/data_sources/__init__.py scripts/refresh_market_data.py tests/test_market_data_service.py tests/test_operations_scripts.py
python3 scripts/refresh_market_data.py --help
```

## Completion

- `YahooChartMarketDataAdapter` converts Yahoo Chart payloads into canonical
  market bars.
- `scripts/refresh_market_data.py --adapter yahoo` is available for explicit
  live refresh.
- Provider tests use a fake HTTP client; no test depends on live internet.
