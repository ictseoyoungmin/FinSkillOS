# Worker, Job Queue & API — Living Spec

> Living document. Update it whenever the worker, the `worker_jobs` queue, the
> System Ops protocols, or the related API contract change. Last updated for
> **Slice 126** (2026-06-02).

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

Each cycle runs **market → news → indicators → regime** inside one
`session_scope()`; the commit happens only at the end, so a mid-cycle exception
rolls back and **no partial data is written** (a provider/network error never
corrupts or duplicates data). An audit row is always recorded — `DONE` with the
cycle summary on success, or `ERROR` with the error type/message on failure.

### Regime recompute (Slice 136)
After the indicator step the cycle **recomputes and persists the market regime**
(`RegimeService.evaluate_today_regime`), gated on
`regime_enabled AND indicator_enabled` — so it runs for `refresh_all` and the
`calculate_indicators` job, and is skipped after a market- or news-only job. This
keeps the dashboard's headline regime consistent with the bars/indicators just
refreshed; previously the regime only updated via the manual `recompute-regime`
protocol and drifted stale. The summary carries a `regime` section
(`status` / `regime` / `riskLevel` / `decisionMode` / `confidence`). Analysis
Workspace also flags a regime `freshness=STALE` when a newer bar exists than the
regime snapshot (Slice 137), as defense for when the worker is paused/down.

### Folder-scoped refresh (Slice 134 / F3)
A `refresh_all` job whose `payload.folder_id` is set collects **only that folder's
members** (subject to the folder's active state + per-type flags) — the base
universe is not unioned. `drain_queue` reads `folder_id` and scopes the cycle's
ticker sets; the cycle audit scope reads `collection:<type>:folder=<id>`.

### Failure handling & recovery
- **No automatic per-job retry.** A failed job is terminal (`status=ERROR`,
  `error` text recorded). Recovery is either the next interval enqueue (dedup
  permits it because `ERROR` is not an *active* status) or a manual System Ops
  re-click. There is no exponential-backoff retry loop today — a persistently
  failing provider produces one `ERROR` job per cadence, visible in Worker Status.
- **Partial provider results do not fail the cycle.** Per-ticker fetch failures
  are captured as counts in the cycle summary (`market.failed` /
  `indicators.failed`) and leave the cycle `OK` with partial coverage; only a
  structural failure (unknown adapter, total fetch failure) raises and marks the
  job `ERROR`. The affected tabs then read `PARTIAL`/`MISSING` coverage honestly
  (see §7), rather than showing stale-as-fresh data.
- **Provider failure modes** (yahoo/yfinance default): rate-limit, network error,
  unsupported symbol, partial fetch, and non-trading-day/holiday gaps all surface
  as reduced succeeded/failed counts + coverage state, not as crashes.
- **Per-ticker retry/backoff** (Slice 148): a transient `MarketDataFetchError` is
  retried within a bounded budget before the ticker is recorded failed —
  `FINSKILLOS_MARKET_FETCH_RETRIES` (default 2 → up to 3 attempts) with exponential
  backoff `FINSKILLOS_MARKET_FETCH_BACKOFF_SECONDS * 2**attempt` (default 1.0s).
  Only the declared transient error is retried; unexpected exceptions fail fast.
  A failed *job* (whole cycle) still has no auto-retry — recovery is the next
  cadence or the Slice-146 "Retry" button. Per-provider circuit-breaking is still
  future work.

### Live-mode toggle (Slice 117)
The cockpit can pause/resume the worker's **automatic** refresh at runtime via a
single-row `worker_control.live_mode` flag (read each cycle, no restart needed).
`POST /api/system-ops/worker-live-mode {liveMode}` sets it; System Ops →
Worker Status shows the toggle. When OFF, the worker skips the start/interval
auto-enqueue but **still drains manually-requested jobs** (the System Ops
refresh buttons keep working).

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

### Runtime overlay settings (Slice 126)

Ops can edit runtime settings from UI (`/api/system-ops/runtime-settings`) and
persist them in `system_ops_settings`. The worker receives that override on each
job execution:

- On startup, effective values are still resolved from environment variables.
- If a DB overlay exists, its keys shadow `.env` for same-name settings.
- `POST /api/system-ops/refresh-*` enqueues payload containing
  `payload.runtime_settings` with the currently effective values.
- `drain_queue()` extracts that map and passes it to `load_config(...,
  runtime_overrides=...)`, so each job runs against the same settings that were
  active when the button was pressed.

---

## 5. Environment variables

| Var | Default | Meaning |
|---|---|---|
| `FINSKILLOS_MARKET_REFRESH_ADAPTER` | `yahoo` | `yahoo` (real) or `mock` (offline) |
| `FINSKILLOS_WORKER_INTERVAL_SECONDS` | `86400` | periodic `refresh_all` cadence |
| `FINSKILLOS_WORKER_POLL_SECONDS` | `5` | queue drain interval |
| `FINSKILLOS_WORKER_RUN_ON_START` | `1` | enqueue a refresh on start |
| `FINSKILLOS_WORKER_{MARKET,NEWS,INDICATOR}_ENABLED` | `1` | per-section toggles |
| `FINSKILLOS_WORKER_REGIME_ENABLED` | `1` | recompute the regime after indicators (Slice 136); gated also on indicators being enabled |
| `FINSKILLOS_MARKET_REFRESH_TICKERS` / `…_INDICATOR_REFRESH_TICKERS` | full 22-ticker cockpit universe | refresh scope — superset of the Analysis index universe so no tab stays MISSING (Slice 116). A present `.env` overrides this. |
| `FINSKILLOS_REFRESH_FOLDER_NAMES` | *(empty)* | folder list for scoped watchlist refresh policy (`all_active` if empty) |
| `FINSKILLOS_EVENT_CALENDAR_ADAPTER` | `mock` | `mock` / `csv` / `http` (+ `…_CSV` / `…_URL`) |
| `system_ops_settings` (table) | persisted key-value JSON | DB-backed runtime override layer. Unset keys fall back to env. |

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
  refresh universe broadened to the full cockpit universe (no MISSING tabs);
  **117** worker live-mode on/off toggle (`worker_control`).
- **126** runtime settings DB overlay (System Ops editable, per-job payload);
  **127–131** folder-driven collection control (System folder seed, per-type
  collection sets, `/api/system-ops/collection-control`, Ops tab, coverage);
  **134** per-folder scoped refresh (`payload.folder_id`); **136** worker
  recomputes regime each cycle (`FINSKILLOS_WORKER_REGIME_ENABLED`); **137**
  regime staleness surfacing; **141** per-folder refresh-scope copy.
- **S7 (this update)** documented failure handling & recovery (no auto-retry;
  partial results don't fail the cycle), provider failure modes, the regime
  recompute coupling, and folder-scoped refresh.
