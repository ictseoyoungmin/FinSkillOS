# 29 — Symbol Subscription and Live Preview

Status: `DONE`
Date: `2026-05-25`

## Goal

Allow arbitrary Symbol Lab searches outside
`FINSKILLOS_MARKET_REFRESH_TICKERS` / `FINSKILLOS_INDICATOR_REFRESH_TICKERS`,
and let the user subscribe/unsubscribe those tickers from the UI.

Subscribed tickers become part of the refresh universe without deleting
historical DB data when later unsubscribed.

## Boundary

Allowed:

- Add a durable `symbol_subscriptions` table.
- Add `POST /api/symbol-lab/{ticker}/subscribe`.
- Add `POST /api/symbol-lab/{ticker}/unsubscribe`.
- Toggle `active` instead of deleting rows.
- Include active subscriptions in System Ops refresh and worker refresh.
- Attempt a provider preview for missing symbols without persisting bars.

Not allowed:

- Delete historical market bars or indicator snapshots on unsubscribe.
- Add brokerage, order, or execution workflows.
- Treat provider preview as a trading signal.

## Runtime Contract

```text
GET /api/symbol-lab?ticker=ADBE
  DB bars exist      -> source=live, dataStatus=OK/PARTIAL
  DB bars missing    -> provider preview attempted, then MISSING if unavailable

POST /api/symbol-lab/ADBE/subscribe
  upsert symbol_subscriptions(active=true)
  attempt provider refresh + indicator calculation
  response subscription.isSubscribed=true

POST /api/symbol-lab/ADBE/unsubscribe
  set symbol_subscriptions(active=false)
  keep market bars / indicators intact
  response subscription.isSubscribed=false
```

Environment knobs:

```text
FINSKILLOS_SYMBOL_PREVIEW_ADAPTER=yahoo
FINSKILLOS_SYMBOL_SUBSCRIBE_ADAPTER=yahoo
```

Tests use `off` / `mock` to avoid external network dependency.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/integration/test_db_migrations.py tests/test_api_symbol_lab.py tests/test_api_v42_contract.py tests/test_operations_scripts.py -q  # 34 passed
python3 -m ruff check api/routes/symbol_lab.py api/routes/system_ops.py api/schemas/symbol_lab.py api/fixtures/symbol_lab.py finskillos/db/models/symbol_subscription.py finskillos/db/repositories/symbol_subscription_repo.py scripts/refresh_worker.py tests/test_api_symbol_lab.py  # passed
docker compose up -d --build api web  # passed
docker compose exec -T api alembic upgrade head  # upgraded to 0008
curl -s -X POST http://localhost:8000/api/symbol-lab/ADBE/subscribe  # isSubscribed=true
curl -s -X POST http://localhost:8000/api/symbol-lab/ADBE/unsubscribe  # isSubscribed=false
docker compose --profile e2e run --rm e2e npm run test:visual  # exit 0; 28 passed, 3 flaky retries passed
```

## Completion

- Subscription rows are durable and can be reactivated.
- Symbol Lab exposes subscription state.
- React renders a Subscribe/Subscribed toggle.
- System Ops and worker refresh include active DB subscriptions in addition to
  env-configured tickers.
- Provider preview/subscribe attempts are isolated from normal DB read paths.
