# 55 — News Intelligence Manual Article Removal

## Goal

Remove the manual news registration surface from News Intelligence.

The tab should:

- stay read-oriented around stored RSS/provider metadata;
- keep source coverage, latest news, impact map, and evidence panels;
- remove the Manual Article Entry UI;
- remove the manual article mutation endpoint and client API helper;
- remove manual article schema/types and tests.

## Out of Scope

- Removing RSS/Atom ingestion.
- Removing System Ops or worker news refresh protocols.
- Changing Catalyst Watch manual event entry.

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

- Removed the News Intelligence Manual Article Entry page mount.
- Deleted the frontend manual article component and CSS.
- Removed the frontend `submitManualArticle` helper, manual article endpoint
  constant, and manual article request/response types.
- Removed `POST /api/news-intelligence/manual-article` and its schema classes.
- Removed `manualEntryRules` from the News Intelligence response contract and
  fixtures.
- Updated API, E2E, and visual specs to treat News Intelligence as a read-only
  stored-news/provider coverage surface.

## Verified

Docker-only checks passed:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_news_intelligence.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "News Intelligence renders"
```
