# 43 — Worker Status Tab And Command Drawer

## Goal

Move Worker Status from a crowded System Ops panel into its own System Ops tab,
and reduce global top navigation pressure.

The system should:

- add a dedicated Worker Status tab for operational worker observability;
- keep System Ops overview focused on health, freshness, sources, and protocols;
- make the worker tab spatially efficient while showing cycle health, component
  state, scope, timing, and recent history;
- replace the top command button text with an icon-only button;
- place the `Command · ⌘K` affordance next to the tab list;
- open command as an in-page drawer instead of a small floating modal/window;
- avoid any trading-action wording.

## Design

The Worker Status tab is a read-only operations view:

```text
GET /api/system-ops workerStatus
  -> System Ops tab state
  -> Worker Status operational visualization
```

The tab should highlight:

- latest cycle status, start/finish, and duration;
- market/news/indicator sub-statuses with scope labels;
- recent cycle history in a compact visual timeline/table;
- error type/detail when present.

The command surface should remain a navigation/command aid only. It should not
create execution/trading affordances.

## Out of Scope

- Starting, stopping, or restarting the worker.
- Scheduling controls or worker interval editing.
- New backend endpoints.
- Reworking every top-level route into nested routes.

## Validation

Use Docker only:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py tests/test_operations_scripts.py tests/integration/test_db_migrations.py -q
```

## Implemented

- Added a System Ops tab switcher with `Overview` and `Worker Status`.
- Moved the Worker Status surface out of the overview panel and into a
  dedicated tab.
- Added compact worker visualization for latest cycle state, component health,
  duration, scope, and recent cycle trace.
- Moved the command affordance next to the global module tab list.
- Converted command/theme tray buttons to icon-only controls.
- Changed the command palette presentation from a small centered modal to a
  right-side drawer.
- Removed the top-tray horizontal scrollbar and hardened narrow viewport
  overflow behavior.

## Verification

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_system_ops.py tests/test_operations_scripts.py tests/integration/test_db_migrations.py -q
docker compose -f docker-compose.yml up -d postgres api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts e2e/theme.spec.ts e2e/responsive.spec.ts e2e/risk-mission-ops.spec.ts --grep-invert "Mission Control renders"
```

Result:

- Docker frontend build passed.
- Docker backend System Ops / worker / migration test scope passed: 33 tests.
- Docker Playwright navigation/theme/responsive/System Ops scope passed: 19 tests.

Resolved follow-up:

- The unrelated Mission Control `mission-capital-map-sector` e2e failure was
  resolved in Slice 44, and full `risk-mission-ops.spec.ts` now passes without
  exclusions.
