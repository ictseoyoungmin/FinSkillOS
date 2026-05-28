# 51 — Trade Memory Journal Mutation UX

## Goal

Close the loop between the React Trade Memory form and the live DB-backed read
model.

The system should:

- keep the existing reflection-only `POST /api/trade-memory/entries` contract;
- refresh the `trade-memory` query after a successful journal entry save;
- show clear success / rejected / error feedback in the form;
- preserve safe wording and avoid execution-style labels.

## Context

Slice 49 promoted `GET /api/trade-memory` to a DB-backed read model. Slice 50
made the live/fixture page state visible. The form already called the POST API,
but the page did not invalidate the read query after a successful save, so a
stored entry could remain invisible until a manual reload.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Trade Memory form stores"
```

## Implemented

- `TradeEntryForm` now accepts an `onSaved` callback.
- `TradeMemoryPage` invalidates the `trade-memory` query after a successful
  journal entry save.
- The existing form feedback remains visible for `OK`, `REJECTED`, and `ERROR`
  results.
- Added an E2E flow that:
  - seeds the sample account;
  - fills a reflection-only journal entry;
  - submits the form;
  - verifies `OK` feedback;
  - verifies the live source state and recent-entry table refresh.

## Verified

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Trade Memory form stores"
```
