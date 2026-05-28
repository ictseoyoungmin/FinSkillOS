# 49 — Trade Memory DB Read Model

## Goal

Promote Trade Memory GET routes from fixture-only snapshots to live DB-backed
reflection read models.

The system should:

- keep `X-FSO-Use-Fixture: 1` as an explicit deterministic fixture mode;
- return live Trade Memory payloads when a DB session is available;
- reuse the existing Slice-12 `build_trade_memory_view_model` and
  `ReflectionService` read model instead of inventing duplicate analytics;
- keep the entry form and POST flow reflection-only;
- preserve descriptive/read-only wording.

## Context

`POST /api/trade-memory/entries` already persists through
`TradeJournalService` when a DB session exists, but `GET /api/trade-memory`
still returns the deterministic fixture. This means a newly stored journal
entry does not appear in the React Trade Memory page until the API read model
is promoted.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_trade_memory.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "navigates primary OS routes"
```

## Implemented

- `GET /api/trade-memory` now returns a live DB-backed response when a DB
  session is available.
- `GET /api/trade-memory/weekly-review` now reads the same live weekly review
  model.
- Fixture mode remains explicit through `X-FSO-Use-Fixture: 1`.
- The live route reuses `build_trade_memory_view_model` plus
  `assert_trade_memory_view_model_is_safe`, then maps the existing Slice-12
  reflection model into the React API schema.
- Legacy stored `BUY` / `SELL` side values are displayed as `LONG` / `SHORT`
  in the API payload so the product surface stays reflection-oriented.
- Added API tests for live Trade Memory reads and live weekly-review reads.

## Verified

```bash
docker compose -f docker-compose.yml build api
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_trade_memory.py -q
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Slice 13.9 promoted routes"
docker exec finskillos-api python -c "..."
```

Live API spot-check:

```text
source=live
headline=Trade Memory is DB-backed; current process read is based on 2 stored entries.
recentEntries=2
weeklyReview.tradeCount=0
```
