# Worker, Job Queue & API — Living Spec

> Living document. Update it whenever the worker, the `worker_jobs` queue, the
> System Ops protocols, or the related API contract change. Last updated for
> **Slice 114** (2026-06-01).

This describes how FinSkillOS keeps the dashboard fresh from **real** market data
without manual steps and without data duplication: a Docker stack that starts
everything together, a request-driven worker, and a Postgres job queue.

---

## 1. Orchestration (`docker compose up`)

`docker compose up` starts these services together (no profile needed):

| Service | Role | Notes |
|---|---|---|
| `postgres` | database | healthcheck-gated |
| `migrate` | one-shot `alembic upgrade head` | `restart: "no"`; gates api + worker via `service_completed_successfully` |
| `api` | FastAPI cockpit backend | depends on postgres healthy + migrate done |
| `web` | Vite React cockpit | depends on api |
| `worker` | refresh worker (this doc) | `restart: unless-stopped`; depends on postgres healthy + migrate done |

Profiled (not started by default): `app` (Streamlit debug), `e2e` (Playwright).

> After pulling a branch with new migrations, rebuild images so the **separate**
> `migrate` image is current: `docker compose build` (or `up --build`).

---

## 2. Worker (`scripts/refresh_worker.py`)

Two modes:

- **`--once`** — run one full refresh cycle directly and exit (used by tests /
  manual runs). Records a `worker_cycle_runs` audit row.
- **daemon** (default) — **queue-driven**:
  1. on start (if `run_on_start`) enqueue a `refresh_all` job;
  2. each poll tick (`FINSKILLOS_WORKER_POLL_SECONDS`, default 5s) **drain the
     queue**: claim the oldest `QUEUED` job, run the matching refresh, record
     `DONE` / `ERROR` with the cycle summary on the job;
  3. every `FINSKILLOS_WORKER_INTERVAL_SECONDS` (default 86400s) enqueue another
     `refresh_all` (dedup-safe).

A failed cycle is logged and the loop continues; **nothing is written on
failure**, so a provider/network error never corrupts or duplicates data.

### Data source
Market refresh defaults to **real data** (`yahoo`); `mock` is explicit opt-in
(`FINSKILLOS_MARKET_REFRESH_ADAPTER=mock`). The mock adapter must never be the
default — it writes synthetic bars on non-trading days that interleave with real
bars and sawtooth the chart.

---

## 3. Job queue — `worker_jobs` (migration `0013`)

| Column | Notes |
|---|---|
| `id` | uuid |
| `job_type` | `refresh_all` / `refresh_market` / `refresh_news` / `calculate_indicators` |
| `status` | `QUEUED` → `RUNNING` → `DONE` \| `ERROR` |
| `dedup_key` | active-job idempotency key (usually = `job_type`) |
| `requested_by` | `worker_start` / `worker_interval` / `system_ops` |
| `payload` / `result` / `error` | JSON / JSON / text |
| `created_at` (monotonic) / `started_at` / `finished_at` | timing |

`WorkerJobRepository`:
- `enqueue(job_type, *, payload=None, requested_by, dedup_key=None)` — **idempotent
  while a job is active**: if a `QUEUED`/`RUNNING` job with the same
  `(job_type, dedup_key)` exists, it is returned instead of inserting a duplicate.
- `claim_next()` — claims the oldest `QUEUED` job → `RUNNING`. On postgres uses
  `SELECT … FOR UPDATE SKIP LOCKED` so concurrent workers never double-claim.
- `complete(job, result)` / `fail(job, error)` / `get` / `list_recent` /
  `count_by_status`.

**No duplication** comes from two layers: idempotent enqueue (no duplicate jobs)
+ upsert-by-`(ticker, timeframe, bar_time)` on write (no duplicate bars).

---

## 4. Request path — System Ops protocols

`POST /api/system-ops/<protocol>` returns a structured `ProtocolRunResult`
(`status` ∈ `OK | NOOP | ERROR | QUEUED`), never a raw stack trace, and records a
`system_ops_protocol_runs` audit row.

| Protocol | Behaviour |
|---|---|
| `refresh-market-data` | **enqueues** `refresh_market` → `QUEUED` |
| `refresh-news` | **enqueues** `refresh_news` → `QUEUED` |
| `calculate-indicators` | **enqueues** `calculate_indicators` → `QUEUED` |
| `seed-sample-account` | synchronous (DB-only) |
| `recompute-regime` | synchronous (DB-only) |
| `run-risk-guards` | synchronous (DB-only) |
| `seed-sample-events` / `refresh-events` | synchronous (DB-only / env-gated adapter) |

The 3 refresh protocols are queued because they may call an external provider;
the worker runs them. The `QUEUED` result's `detailEvidence` carries `job_type`
and `job_id`. Enqueue is dedup-safe, so repeated clicks while a job is pending
return the same job. When no DB session is reachable, protocols return `NOOP`
(`no_database_session`) and never touch production.

---

## 5. Environment variables

| Var | Default | Meaning |
|---|---|---|
| `FINSKILLOS_MARKET_REFRESH_ADAPTER` | `yahoo` | `yahoo` (real) or `mock` (offline) |
| `FINSKILLOS_WORKER_INTERVAL_SECONDS` | `86400` | periodic `refresh_all` cadence |
| `FINSKILLOS_WORKER_POLL_SECONDS` | `5` | queue drain interval |
| `FINSKILLOS_WORKER_RUN_ON_START` | `1` | enqueue a refresh on start |
| `FINSKILLOS_WORKER_{MARKET,NEWS,INDICATOR}_ENABLED` | `1` | per-section toggles |
| `FINSKILLOS_MARKET_REFRESH_TICKERS` / `…_INDICATOR_REFRESH_TICKERS` | full 22-ticker cockpit universe | refresh scope — superset of the Analysis index universe so no tab stays MISSING (Slice 116). A present `.env` overrides this. |
| `FINSKILLOS_EVENT_CALENDAR_ADAPTER` | `mock` | `mock` / `csv` / `http` (+ `…_CSV` / `…_URL`) |

---

## 6. Testing guarantees

- Tests are isolated from production: an autouse conftest fixture points each
  test's `DATABASE_URL` at an unreachable address (so an un-set test gets
  `session=None`, the offline path) and forces the `mock` adapter — so the suite
  never reaches the network and never writes to the live DB. Proven: a Docker
  `pytest` run leaves prod `mock` bars = 0.
- Audit `created_at` is strictly monotonic so same-microsecond runs order
  deterministically.

---

## 7. Data-source state contract (cockpit tabs)

Every product tab resolves to exactly one honest state — fixture content is never
substituted as analysis on a reachable DB:

| Trigger | `source` | `systemStatus.db` | Meaning |
|---|---|---|---|
| `X-FSO-Use-Fixture: 1` | `fixture` | `LIVE` | deterministic sample (visual QA opt-in) |
| `session is None` (no DB) | `fixture` | `MISSING` | db-unavailable banner + sample placeholder |
| reachable DB, **rows** | `live` | `LIVE` | real read model |
| reachable DB, **no rows** | `live` | `LIVE` | explicit live-empty / MISSING (no sample) |
| reachable DB, read raised | `live` | `LIVE` | live-error narrative (class name only) |

Guarded by `tests/test_reachable_empty_is_live.py` (all 9 tabs). Seeded *sample*
rows (e.g. `seed-sample-account` / `seed-sample-events`) are real `live` rows;
remove them to make the tabs show MISSING until real data exists.

---

## Change log
- **111** real-data default + test isolation; **112** orchestration (migrate +
  worker auto-start); **113** `worker_jobs` queue + queue-driven worker; **114**
  System Ops refresh protocols enqueue jobs (request path) + cockpit `QUEUED`;
  **115** reachable-empty → live(-empty) guard + sample-data cleanup; **116**
  refresh universe broadened to the full cockpit universe (no MISSING tabs).
