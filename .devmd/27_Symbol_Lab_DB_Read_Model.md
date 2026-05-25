# 27 — Symbol Lab DB Read Model

Status: `DONE`
Date: `2026-05-25`

## Goal

Promote `GET /api/symbol-lab` from fixture-first only to a DB-backed read
model when stored market bars are available.

The React page remains render-only. It calls FastAPI, and FastAPI reads local
DB snapshots. No provider, image, quote, brokerage, order, or execution call is
made during page rendering.

## Symbol Image Decision

Symbol images/logos are possible, but they need a provider, local cache,
attribution, failure fallback, and visual baseline policy. This slice does not
fetch logo URLs during render. The live response explicitly keeps symbol image
retrieval deferred to a later provider/cache slice.

## Boundary

Allowed:

- Read stored market bars and indicator snapshots for any searched ticker.
- Attach current position context when the ticker exists in `positions`.
- Attach active alerts when the alert payload or text matches the ticker.
- Return `MISSING` instead of fixture bars when the DB is reachable but the
  ticker has no stored bars.
- Keep `X-FSO-Use-Fixture: 1` as the visual/test override.

Not allowed:

- Fetch external provider data during `GET /api/symbol-lab`.
- Fetch symbol images/logos during `GET /api/symbol-lab`.
- Add brokerage, order, or execution workflows.
- Fill DB gaps with fixture bars once live DB mode is active.

## Runtime Contract

```text
GET /api/symbol-lab?ticker=SPY

X-FSO-Use-Fixture: 1     -> fixture
DB unavailable           -> fixture fallback
DB reachable + bars      -> source=live, dataStatus=OK/PARTIAL
DB reachable + no bars   -> source=live, dataStatus=MISSING
```

`dataStatus=PARTIAL` means stored bars exist but indicator snapshots have not
been calculated after refresh.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_symbol_lab.py tests/test_api_v42_contract.py -q  # 22 passed
python3 -m ruff check api/routes/symbol_lab.py tests/test_api_symbol_lab.py tests/test_api_v42_contract.py  # passed
timeout 60 python3 -m pytest tests/test_api_symbol_lab.py tests/test_api_market_kernel.py tests/test_api_v42_contract.py tests/test_operations_scripts.py -q  # 42 passed
python3 -m ruff check api/routes/symbol_lab.py tests/test_api_symbol_lab.py tests/test_api_v42_contract.py tests/test_operations_scripts.py scripts/refresh_worker.py  # passed
docker compose up -d --build api web  # passed
curl -s http://localhost:8000/api/symbol-lab?ticker=SPY  # source=live, dataStatus=OK
docker compose --profile e2e run --rm e2e npm run test:visual  # exit 0; 28 passed, 3 flaky retries passed
git diff --check  # passed
```

## Completion

- Symbol Lab can read stored bars and latest usable indicator snapshots.
- Future-dated bars and indicator snapshots are ignored.
- Position and alert context attach from the DB when available.
- Missing ticker state is explicit and live-aware.
- v4.2 contract test now treats Symbol Lab as live-capable.
