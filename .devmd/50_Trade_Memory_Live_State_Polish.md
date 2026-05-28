# 50 — Trade Memory Live State Polish

## Goal

Make Trade Memory's live DB-backed state visible in the React page.

The system should:

- distinguish deterministic fixture samples from live DB-backed journal reads;
- make an empty live journal feel intentional, not unfinished;
- show stored entry count and current weekly review count near the top of the
  page;
- keep the page reflection-only and free of execution controls.

## Context

Slice 49 promoted `GET /api/trade-memory` to a live DB-backed read model. The
React page still rendered the same layout without a clear source/state cue, so
an empty live journal could look like missing content rather than a valid DB
state.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Trade Memory"
```

## Implemented

- Added a top-of-page Trade Memory source/state band.
- The band distinguishes:
  - deterministic fixture samples;
  - live DB with stored journal entries;
  - live DB with an empty journal.
- The band shows stored entry count, current weekly review count, and source.
- Added an E2E assertion that the promoted Trade Memory route exposes the
  source/state band.

## Verified

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts -g "Slice 13.9 promoted routes"
docker compose -f docker-compose.yml --profile e2e run --rm e2e node -e "..."
```

Live render spot-check:

```text
LIVE DB Stored journal read model
ENTRIES 3
WEEKLY 0
SOURCE LIVE
```
