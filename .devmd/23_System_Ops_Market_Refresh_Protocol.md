# 23 — System Ops Market Refresh Protocol

Status: `DONE`
Date: `2026-05-25`

## Goal

Wire market-bar refresh into the System Ops UI/API protocol surface so the
user does not need to run the CLI for the common local operation.

## Boundary

Allowed:

- Add a System Ops protocol card for refreshing stored market bars.
- Run `MarketDataService.refresh_bars` from a POST protocol.
- Keep the default adapter offline-safe (`mock`).
- Allow live Yahoo refresh only through explicit configuration.
- Return structured run evidence and append it to the protocol audit log.

Not allowed:

- Fetch market data during normal product page rendering.
- Turn Market Kernel or Symbol Lab into live read models in this slice.
- Add brokerage, order, or execution workflows.
- Make visual baselines depend on network access.

## Runtime Contract

```text
POST /api/system-ops/refresh-market-data
DB unavailable                         -> status=NOOP
DB available, default configuration    -> adapter=mock refresh
FINSKILLOS_MARKET_REFRESH_ADAPTER=yahoo -> Yahoo Chart adapter refresh
```

Optional environment knobs:

```text
FINSKILLOS_MARKET_REFRESH_ADAPTER=mock|yahoo
FINSKILLOS_MARKET_REFRESH_TICKERS=SPY,QQQ,TSLA
```

The protocol remains operational and descriptive. Product tabs still need a
separate DB read-model promotion before they show stored market bars.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_system_ops.py tests/test_api_health.py -q  # 15 passed
timeout 60 python3 -m pytest tests/test_api_v42_contract.py tests/test_market_data_service.py tests/test_operations_scripts.py -q  # 26 passed
python3 -m ruff check api/routes/system_ops.py api/routes/health.py api/schemas/system_ops.py api/fixtures/system_ops.py tests/test_api_system_ops.py tests/test_api_health.py tests/conftest.py  # passed
docker compose --profile e2e run --rm e2e npm run build  # passed
docker compose up -d --build api web  # passed
docker compose --profile e2e run --rm e2e npm run test:visual  # 31 passed
```

## Completion

- System Ops catalogue includes `refresh_market_data`.
- Frontend System Ops can invoke the protocol through the existing protocol
  card flow.
- DB-backed mock refresh is test-covered with a temporary SQLite database.
