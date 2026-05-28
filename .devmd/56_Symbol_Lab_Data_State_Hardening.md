# 56 — Symbol Lab Data State Hardening

## Goal

Harden Symbol Lab's live/fixture/missing-data state.

The tab should:

- expose chart, indicator, logo, subscription, and provider state explicitly;
- show a compact state band near the top of the page;
- keep missing chart evidence descriptive instead of looking unfinished;
- preserve arbitrary ticker search and subscription behavior;
- avoid provider calls during render beyond the existing Symbol Lab boundary.

## Out of Scope

- New market data providers.
- Trading, brokerage, or execution actions.
- Reworking foldered subscriptions.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_symbol_lab.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Symbol Lab"
```

## Implemented

- Added `dataState` to the Symbol Lab API contract.
- `dataState` reports chart status, chart evidence source, bar count,
  indicator status, logo source, subscription status, and provider note.
- Fixture and live DB-backed responses now both populate `dataState`.
- Symbol Lab renders a compact state band for source, chart, indicators, logo,
  and refresh-universe membership.
- Existing live-aware search behavior remains intact for stored tickers,
  arbitrary tickers, and macro proxies.
- E2E expectations no longer assume a fixed fixture shortcut count or a live
  TSLA position row.

## Verified

Docker-only checks passed:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_symbol_lab.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/market-analysis-symbol.spec.ts -g "Symbol Lab"
```
