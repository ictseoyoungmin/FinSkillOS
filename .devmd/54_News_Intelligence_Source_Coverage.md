# 54 — News Intelligence Source Coverage

## Goal

Harden News Intelligence around source confidence and provider coverage.

The tab should:

- expose source coverage as an explicit API contract;
- distinguish article count from distinct-provider coverage;
- show latest provider timestamp and provider mix near the top of the page;
- keep empty/live states descriptive instead of looking unfinished;
- preserve short-summary and no-execution wording contracts.

## Out of Scope

- Adding new external news providers.
- Fetching provider data during page render.
- Full article storage.
- Trading or brokerage actions.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_news_intelligence.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "News Intelligence renders"
```

## Implemented

- Added `sourceCoverage` to the News Intelligence API contract with article
  count, distinct provider count, latest published timestamp, confidence,
  provider mix, and coverage note.
- Fixture and live DB-backed responses now both populate source coverage.
- News Intelligence renders a compact source coverage band under the top
  judgment row.
- News Impact Map keeps its test/render contract in both grouped and empty
  states.
- Manual Article Entry was briefly remounted during this slice, then removed
  in Slice 55 because manual news registration is not part of the desired
  product surface.
- API tests now explicitly use fixture mode when asserting fixture-only
  timestamp and forbidden-wording contracts, avoiding accidental live DB
  coupling.

## Verified

Docker-only checks passed:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_news_intelligence.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "News Intelligence renders"
```
