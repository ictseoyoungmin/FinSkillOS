# 52 — Trade Memory Form Ergonomics

## Goal

Make the Trade Memory journal form easier to use repeatedly.

The system should:

- group fields by journal intent instead of one long flat form;
- default the journal date to today;
- show compact required-field and tag-count state;
- provide a reset action;
- keep the existing successful save -> live read refresh behavior;
- preserve reflection-only wording.

## Out of Scope

- Editing existing journal entries.
- Deleting journal entries.
- Broker/execution integrations.
- New backend fields.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Trade Memory form"
```

## Implemented

- Trade date now defaults to the current local ISO date for new journal
  entries.
- The journal form is grouped into entry context, setup tags, outcome, and
  reflection sections.
- A compact form state row reports required-field readiness, selected tag
  count, and current side.
- Client-side required-field validation prevents empty date/ticker submission
  and keeps the save button disabled until the minimum journal context is
  ready.
- A reset action clears the form back to the current-date default without
  disturbing the live read refresh behavior after successful saves.

## Verified

Docker-only checks passed:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Trade Memory form"
```
