# 46 — System Ops Health Freshness Polish

## Goal

Make the System Ops overview feel finished and scan-friendly.

The system should:

- replace raw `System Health` text with compact status metrics;
- replace raw freshness timestamp text with a dense freshness grid;
- keep exact timestamps available without letting long ISO strings dominate the
  panel;
- prevent short `LIVE` status chips from inflating data-source card height;
- preserve descriptive/read-only wording.

## Out of Scope

- New backend freshness fields.
- New provider integrations.
- Worker controls or scheduling.
- Trading-action wording or controls.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
```

## Implemented

- Replaced raw `System Health` paragraphs with compact API / DB / Mode /
  Source / Completeness status tiles.
- Replaced raw freshness timestamp text with a six-item freshness grid. Exact
  ISO values remain available via hover title, while the visible text stays
  short enough for the panel.
- Tightened the data-source strip so status chips keep a stable top-right
  position and details clamp to two lines.
- Added a visual screenshot check at desktop width:
  `frontend/test-results/system-ops-polish.png`.

## Verified

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/risk-mission-ops.spec.ts -g "System Ops renders"
docker compose -f docker-compose.yml --profile e2e run --rm e2e node -e "..."
```

Screenshot layout check:

```text
System Health panel: 925x223
Freshness Status panel: 925x223
Data-source cards: 460x75 each
```
