# 14 — Deployment and Operations

## Goal

Define local deployment, backup, migration, health, recovery, and visual
gate practices for the current FinSkillOS product architecture:

```text
finskillos/       Python domain/service/db core
api/              FastAPI read-only adapter + System Ops protocols
frontend/         Vite React v4.2 Evidence-to-Judgment cockpit
docker-compose    Postgres + API + Web + optional Streamlit debug/admin + e2e
```

This slice replaces the older Streamlit-first deployment plan. Streamlit
remains available through the `app` compose profile, but it is no longer
the primary product UI.

## Product boundary

FinSkillOS is a personal investment OS for:

```text
market state
risk interpretation
portfolio constraints
watchpoints
reflection support
operational protocols
```

Do not add:

```text
buy/sell recommendations
order placement
brokerage execution
direct trading actions
price-direction commands
```

The FastAPI app may expose read-only snapshots and idempotent System Ops
protocols only.

## Current local deployment target

Recommended everyday runtime:

```text
Docker Postgres
FastAPI api service        http://localhost:8000
Vite React web service     http://localhost:5173
Playwright e2e profile     on demand only
Streamlit app profile      debug/admin only, http://localhost:8501
```

Baseline commands:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:e2e
docker compose --profile e2e run --rm e2e npm run test:visual
docker compose stop
docker compose start
```

Debug/admin commands:

```bash
docker compose --profile app up --build app
```

Avoid routine volume deletion. `docker compose down -v` is destructive
for local Postgres state and should be reserved for intentional reset
work.

## Migration operation

The DB schema is still owned by the Python core. Apply migrations before
using live DB-backed routes or System Ops protocols:

```bash
docker compose up -d postgres
docker compose run --rm app alembic upgrade head
```

If the Streamlit debug/admin image is not desired, add an API/admin-safe
migration command in this slice so migrations can run without presenting
Streamlit as the primary runtime.

Acceptance:

```text
- Document the canonical migration command.
- Verify alembic upgrade head is idempotent.
- Document recovery for missing-column errors.
```

## Fixture mode vs live mode

The React cockpit is currently fixture-first for deterministic UI and
visual QA. Slice 14 must make the boundary explicit:

```text
fixture
  Deterministic v4.2 snapshots, safe for Playwright baselines and no-DB
  rendering.

live
  DB-backed snapshots derived from stored bars, indicators, regimes,
  portfolio snapshots, news, event, and journal rows.

fallback
  UI may render a cached local fixture only when the API is unreachable,
  and must label the data source clearly.
```

Acceptance:

```text
- Every API snapshot has `generatedAt` / `generated_at`.
- Every API snapshot exposes `source` as fixture or live.
- System Ops shows data-source pills for DB, market data, news/events,
  and visual QA state.
- DB connection failure is visible as operational status, not hidden as
  a fake live snapshot.
```

## Freshness and health contract

Extend `/api/health` or add `/api/system-status` so the product can
answer "how fresh is this judgment?" without relying on ad hoc page
copy.

Target fields:

```text
generatedAt
mode
apiStatus
dbStatus
source
latestPortfolioSnapshotAt
latestMarketBarAt
latestIndicatorAt
latestRegimeAt
latestNewsAt
latestEventAt
staleFlags
protocolAvailability
```

Stale policy:

```text
- Market data failure: keep last known regime, show stale timestamp, do
  not recompute from incomplete data.
- News fetch failure: do not block the cockpit; mark News Intelligence
  stale.
- Event refresh failure: preserve stored events; mark Catalyst Watch
  stale.
- DB failure: show API reachable but DB unavailable; System Ops
  protocols return structured ERROR or NOOP.
```

## Backup and restore

Postgres backup:

```bash
mkdir -p backups
docker compose exec postgres pg_dump -U finskillos -d finskillos > backups/finskillos_YYYYMMDD.sql
```

Postgres restore drill:

```bash
docker compose stop api web app
docker compose exec -T postgres psql -U finskillos -d finskillos < backups/finskillos_YYYYMMDD.sql
docker compose start api web
```

Local runtime data to preserve:

```text
data/parquet/
data/exports/
data/logs/
frontend/e2e/visual/*-snapshots/
frontend/playwright-report/      generated artifact, optional
frontend/test-results/           generated artifact, optional
```

Acceptance:

```text
- Document backup location and retention expectation.
- Test one backup command against the compose Postgres service.
- Document that visual baseline PNGs are source artifacts, not runtime
  cache.
```

## Visual gate operation

Use Docker for visual baselines so font/DPI output matches the intended
gate:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:e2e
docker compose --profile e2e run --rm e2e npm run test:visual
docker compose --profile e2e run --rm e2e npm run test:visual:layout
```

Only regenerate baselines for intentional UI changes:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual:update
```

Reference:

```text
frontend/e2e/visual/README.md
```

## Scheduler and refresh policy

Do not introduce Celery/Redis in this slice unless a concrete runtime
need is demonstrated. Start with documented commands and System Ops
protocols:

```text
seed sample account
seed sample events
refresh stored market data
calculate indicators
recompute regime
run risk guards
```

Acceptance:

```text
- Document whether each refresh is manual, script-driven, or future
  scheduled work.
- Do not make live refresh implicit if stale/error status is not visible.
- Keep protocol wording descriptive: "refresh", "recompute",
  "evaluate", "seed"; never "execute trade" or order-like language.
```

## Observability

Log or surface:

```text
API health
DB connection status
data refresh duration
indicator calculation duration
regime calculation duration
risk guard evaluation duration
protocol result status
cache hit/miss when cache exists
visual gate pass/fail command output
```

## Documentation updates required in this slice

Update:

```text
README.md
docs/v2_1/CONTEXT_INDEX.md
docs/v2_1/10_Deployment_Operations.md if it still contradicts this slice
frontend/e2e/visual/README.md if commands or tolerances change
```

README must present:

```text
1. React/FastAPI/Postgres quickstart first.
2. Streamlit as debug/admin only.
3. Fixture/live mode boundary.
4. Backup/restore warning for DB volumes.
5. Visual gate commands.
```

## Completion checklist

```text
Status: TODO
Implemented operations:
- [ ] React/FastAPI/Postgres local compose path documented and verified
- [ ] Migration command documented and verified
- [ ] Backup command documented and verified
- [ ] Restore drill documented
- [ ] Fixture vs live operational contract documented
- [ ] Health/freshness contract implemented or explicitly deferred
- [ ] System Ops protocol wording checked for safety
- [ ] Visual gate commands verified in Docker profile
- [ ] README and context index updated

Known issues:
- fixture-first routes are acceptable through Slice 13.11, but Slice 14
  must label that boundary more clearly for local product use.
```
