# 25 — System Ops Indicator Calculate Protocol

Status: `DONE`
Date: `2026-05-25`

## Goal

Add a System Ops protocol for calculating descriptive indicator snapshots from
stored market bars.

This closes the immediate gap after Slice 24: Market Kernel can read stored
bars, but it reports `dataStatus=PARTIAL` until indicator snapshots exist.

## Worker Decision

No worker is needed for this slice.

The current product target is local, manual-first, and cron-compatible. Indicator
calculation is a bounded operational task that can run through the System Ops
POST protocol or the existing CLI script. Celery/Redis/background workers remain
deferred until refresh duration, multi-user concurrency, or scheduled always-on
operation makes them necessary.

## Boundary

Allowed:

- Add a System Ops protocol card for indicator calculation.
- Run `SignalService.compute_for_universe` against stored DB bars.
- Keep results descriptive: RSI, EMA, Bollinger position, volume z-score,
  momentum score, trend state.
- Return structured run evidence and audit log entries.

Not allowed:

- Fetch provider data in the indicator protocol.
- Add a background worker.
- Emit trading/order/execution language.

## Runtime Contract

```text
POST /api/system-ops/calculate-indicators
DB unavailable                  -> status=NOOP
DB available, no bars           -> status=NOOP
DB available, sufficient bars   -> status=OK, snapshots upserted
```

Optional environment knob:

```text
FINSKILLOS_INDICATOR_REFRESH_TICKERS=SPY,QQQ,TSLA
```

When omitted, the protocol uses the same focus universe as market refresh.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_system_ops.py tests/test_api_health.py tests/test_api_market_kernel.py tests/test_api_v42_contract.py tests/test_market_data_service.py -q  # 48 passed
python3 -m ruff check api/routes/system_ops.py api/routes/market_kernel.py api/routes/health.py api/schemas/system_ops.py api/fixtures/system_ops.py finskillos/services/signal_service.py tests/test_api_system_ops.py tests/test_api_health.py tests/test_api_market_kernel.py tests/test_api_v42_contract.py tests/conftest.py  # passed
docker compose --profile e2e run --rm e2e npm run build  # passed
docker compose up -d --build api web  # passed
curl -s -X POST http://localhost:8000/api/system-ops/calculate-indicators  # status=OK, 12 snapshots written
curl -s -i http://localhost:8000/api/market-kernel?ticker=SPY  # 200, source=live, dataStatus=OK
docker compose --profile e2e run --rm e2e npm run test:visual  # exit 0; 28 passed, 3 flaky retries passed
```

## Completion

- System Ops catalogue includes `calculate_indicators`.
- Frontend System Ops can invoke the protocol through the existing card flow.
- DB-backed indicator calculation is test-covered with a temporary SQLite DB.
