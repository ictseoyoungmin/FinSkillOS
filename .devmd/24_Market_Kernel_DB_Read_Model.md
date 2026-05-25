# 24 — Market Kernel DB Read Model

Status: `DONE`
Date: `2026-05-25`

## Goal

Promote `/api/market-kernel` from fixture-only to a DB-backed read model for
stored market bars and indicator snapshots.

This follows Slice 23: the UI can now refresh market bars through System Ops,
and Market Kernel can read those stored bars without calling a provider during
page rendering.

## Boundary

Allowed:

- Read stored `market_bars` and latest `indicator_snapshots`.
- Return `source=live` when the DB is reachable.
- Return `dataStatus=MISSING` when the requested ticker has no stored bars.
- Keep `X-FSO-Use-Fixture: 1` as the deterministic visual/test override.

Not allowed:

- Call Yahoo or any live provider from `GET /api/market-kernel`.
- Emit trade/order/execution language.
- Promote Symbol Lab or Analysis Workspace in this slice.

## Runtime Contract

```text
X-FSO-Use-Fixture: 1          -> deterministic fixture
DB unavailable                -> deterministic fixture
DB available, ticker bars     -> source=live, dataStatus=OK/PARTIAL
DB available, no ticker bars  -> source=live, dataStatus=MISSING
```

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_market_kernel.py tests/test_api_v42_contract.py -q  # 17 passed
python3 -m ruff check api/routes/market_kernel.py tests/test_api_market_kernel.py tests/test_api_v42_contract.py  # passed
timeout 60 python3 -m pytest tests/test_api_system_ops.py tests/test_api_health.py tests/test_api_market_kernel.py tests/test_api_v42_contract.py -q  # 32 passed
docker compose up -d --build api web  # passed
curl -s -X POST http://localhost:8000/api/system-ops/refresh-market-data  # OK, 12 symbols
curl -s http://localhost:8000/api/market-kernel?ticker=SPY  # source=live, dataStatus=PARTIAL
docker compose --profile e2e run --rm e2e npm run test:visual  # 31 passed
```

## Completion

- Market Kernel reads DB-backed bars and latest indicators when available.
- Missing stored data is explicit instead of silently swapping in dummy data.
- Visual baselines remain fixture-deterministic through the existing fixture
  header override.
