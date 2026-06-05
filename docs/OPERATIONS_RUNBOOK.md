# FinSkillOS — Daily Operations Runbook

Practical operator loop for running FinSkillOS locally via Docker Compose. This is
the "how do I actually use it every day" doc. Architecture/contracts live in
`.devmd/CURRENT_STATE.md`, `docs/WORKER_QUEUE_AND_API_SPEC.md`, and
`docs/v2_1/13_State_Vocabulary_And_Data_Source_Contract.md`.

All commands run from the repo root. Everything is Docker — no host Python/Node.

## Operator CLI — `fsoctl.sh` (Slice 169)

`./fsoctl.sh` is the one-command entrypoint that wraps the workflow below. Run
`./fsoctl.sh help` for the full surface. Common commands:

```bash
./fsoctl.sh setup            # first-time: build → DB → migrate → seed → start
./fsoctl.sh up               # start the stack   ./fsoctl.sh down   # stop (keeps data)
./fsoctl.sh status           # service states    ./fsoctl.sh logs worker
./fsoctl.sh refresh          # one refresh cycle now
./fsoctl.sh backup           # → backups/finskillos_<ts>.sql
./fsoctl.sh restore <file> --confirm-restore
./fsoctl.sh build            # rebuild app images (do this after editing app code)
./fsoctl.sh verify           # rebuild app images, then run the Docker test gate
```

`build`/`verify` rebuild first because the app services bake their source at build
time (no bind-mount), so a `run`/`up` against edited code needs a fresh image. The
raw `docker compose …` commands below are what each wrapper runs.

## Services (docker-compose.yml)

| Service | Role | Port |
|---|---|---|
| `postgres` | database (volume `postgres_data`, persists across restarts) | 5432 |
| `migrate` | one-shot `alembic upgrade head`, then exits | — |
| `api` | FastAPI read-only adapter + System Ops protocols | 8000 |
| `web` | React/Vite cockpit (dev server) | 5173 |
| `worker` | `scripts/refresh_worker.py` queue-driven refresh loop | — |
| `app` (profile `app`) | Streamlit debug/admin UI | 8501 |
| `e2e` (profile `e2e`) | Playwright visual/e2e image | — |
| `web-release` (profile `release`) | nginx static serve of the built bundle | 8080 |

Cockpit: **http://localhost:5173** · API: **http://localhost:8000/api**.

## Local data-dir policy (Slice 172)

Where local state lives — `./fsoctl.sh info` reports it:

| Location | What | Lifecycle |
|---|---|---|
| `postgres_data` (Docker named volume) | the database | survives `docker compose down`; **`down -v` erases it** |
| `backups/` (`BACKUP_DIR`) | pg_dump backups | host directory; gitignored except `.gitkeep` |
| `data/` (`DATA_DIR` / `CACHE_DIR` / `EXPORT_DIR`) | caches / exports | host directories, created on demand |
| `.env` | local config overrides | optional; `.env.example` is the template |

Rules: never `docker compose down -v` unless you intend to erase the database;
back up before risky changes (`./fsoctl.sh backup` / `drill`); to relocate
backups, set `BACKUP_DIR` in `.env`.

## Local release profile (Slice 172)

`web` runs the Vite dev server (:5173). For a stable local instance, the
`release` profile serves the **built** bundle via nginx (static + `/api` proxy):

```bash
./fsoctl.sh release        # build + start web-release → http://localhost:8080
./fsoctl.sh release-down   # stop it
# raw: docker compose --profile release up -d web-release
```

It is opt-in and started explicitly, so it never collides with the dev `web`
service on the default `docker compose up`.

## First-time setup

```bash
docker compose build                      # build api / web / worker / migrate
docker compose up -d postgres             # start DB
docker compose run --rm migrate           # apply migrations (0001 … head)
docker compose run --rm api python -m scripts.seed_sample_data
                                          # seed sample account + System folder (22 leaders)
                                          # (no --no-deps: needs the DB on the compose network)
docker compose up -d                      # start api + web + worker
```

Then open http://localhost:5173. `seed_sample_data` is idempotent — safe to re-run.

## Daily start / stop / status

```bash
docker compose up -d            # start everything (brings up deps)
docker compose ps               # service states
docker compose stop             # stop (keeps the DB volume / data)
docker compose logs -f worker   # follow the worker
curl -s localhost:8000/api/health
```

A `docker compose up -d` after edits to app code needs a rebuild first
(`docker compose build api web worker`) — this compose uses image contents, not a
live bind mount.

## The daily loop

1. **Start** the stack (`docker compose up -d`), open the cockpit.
2. **Check state** on each tab — every tab declares one honest state (see below).
3. **Refresh** when data is stale: either let the worker run (live mode on) or
   trigger a System Ops protocol / per-folder "Refresh now".
4. **Read** the evidence: regime, coverage, freshness, watchpoints. Output is
   descriptive only — no buy/sell.

## Reading state (vocabulary)

- **source** — `live` (DB rows) vs `fixture` (deterministic sample; only on the
  `X-FSO-Use-Fixture` opt-in or when the DB is unreachable).
- **db** — `LIVE` (reachable) / `MISSING` (reachable, no rows) / `UNAVAILABLE`
  (no DB). A reachable-but-empty DB shows `live` + empty, never a fixture sample.
- **freshness** — `FRESH` / `STALE` / `MISSING`. Control Room rails compare the
  latest bar/event to today against `FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS`
  (default 3). Analysis Workspace marks the **regime** `STALE` when a newer bar
  exists than the regime snapshot.
- **coverage** — `COMPLETE` / `PARTIAL` / `SPARSE` / `MISSING` with an evidence %.
  PARTIAL distinguishes complete rows, bars-without-indicators, and missing.

## Refresh & collection

- **Worker (automatic):** runs each poll tick; refreshes market → news →
  indicators → regime. Toggle automatic refresh without restart:
  System Ops → Worker Status, or
  `curl -X POST localhost:8000/api/system-ops/worker-live-mode -H 'Content-Type: application/json' -d '{"liveMode": false}'`.
  When off, manual System Ops refreshes still run.
- **System Ops protocols (manual):** `seed-sample-account`, `seed-system-folder`,
  `refresh-market-data`, `refresh-news`, `calculate-indicators`,
  `recompute-regime`, `run-risk-guards`, `seed-sample-events`, `refresh-events`.
  The three refresh ones **enqueue a worker job** (return `QUEUED`); the rest are
  synchronous. Re-clicking while a job is pending is dedup-safe.
- **Collection Control (System Ops tab):** add tickers to folders; toggle
  Active / Price / Indicators / News per folder or globally; the worker collects
  per folder. **"Refresh now" on a folder refreshes that folder's symbols only —
  not the global universe**, and excludes inactive folders / disabled types.
- **Adapter:** real data (`yahoo`) is the default; `mock` is explicit opt-in
  (`FINSKILLOS_MARKET_REFRESH_ADAPTER=mock`) — never leave mock on in normal use.

## Recover

- **A refresh failed (job ERROR):** failures don't corrupt data (a cycle commits
  only at the end). A failed job is terminal; it re-runs on the next interval, or
  re-click the System Ops refresh. Partial provider failures (some tickers) leave
  the cycle `OK` with PARTIAL coverage — they are counts in the cycle summary, not
  a crash. (Provider retry/backoff is a known gap — roadmap Phase 1/148.)
- **Regime looks wrong / stale:** the worker recomputes it each cycle; force it
  with the `recompute-regime` protocol (or `calculate-indicators`, which also
  recomputes regime).
- **Worker idle:** check `docker compose logs worker`; confirm live mode is on and
  the queue isn't blocked (`docker compose ps`). Restart: `docker compose restart worker`.
- **DB unavailable banner:** check `docker compose ps postgres`; start it
  (`docker compose up -d postgres`). The cockpit degrades to an explicit
  db-unavailable state, not fake data.
- **Synthetic (mock) bars or orphan indicator snapshots crept in:** the System Ops
  Worker Status tab shows Provenance (synthetic-source tickers) + Invariants
  (orphan snapshots). The "Data Repair" panel previews a cleanup (dry-run) and only
  deletes synthetic bars + orphan snapshots after you confirm — real bars are never
  touched. Back up first. (`POST /api/system-ops/data-repair` dry-run;
  `?confirm=true` to apply.)

## Backup / restore

```bash
bash scripts/backup_postgres.sh                  # → backups/finskillos_YYYYMMDD_HHMMSS.sql
bash scripts/restore_postgres.sh backups/finskillos_YYYYMMDD_HHMMSS.sql --confirm-restore
```

Restore requires the explicit `--confirm-restore` (or `FINSKILLOS_CONFIRM_RESTORE=1`)
and uses confirmed clean-restore semantics. Back up before a risky migration or a
data-repair protocol.

### Backup-restore drill (Slice 171)

A backup is only as good as its last verified restore. Two levels:

```bash
./fsoctl.sh drill                  # back up to backups/, then verify the dump
```

`drill` runs `scripts/backup_verify.py`, which checks the dump is non-trivial,
ends with pg_dump's completion marker (not truncated), and declares every core
table (`accounts`, `portfolio_snapshots`, `positions`, `trades`, `market_bars`,
`alembic_version`). Status `OK` (exit 0) / `SUSPECT` (exit 3) / `MISSING` (exit 4).

**Full drill** — prove a dump actually restores, without touching live data, by
restoring into a throwaway database:

```bash
docker compose exec -T postgres createdb -U finskillos finskillos_drill
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U finskillos \
  -d finskillos_drill < backups/<dump>.sql
docker compose exec -T postgres psql -U finskillos -d finskillos_drill \
  -c "select count(*) from accounts;"      # sanity check
docker compose exec -T postgres dropdb -U finskillos finskillos_drill
```

Run the full drill periodically and before any risky migration / restore.

## Migration safety preflight (Slice 170)

Before an upgrade or restore, check the DB revision against the code's migration
head:

```bash
./fsoctl.sh check                  # or: docker compose run --rm api python scripts/migration_safety_check.py
```

States: `UP_TO_DATE` / `PENDING_UPGRADE` (run `./fsoctl.sh migrate`) /
`UNINITIALISED` (fresh DB) / `UNKNOWN_REVISION` (**the DB is at a revision the
code doesn't know — the code is likely older than the DB; align the code version
before upgrading**, exit 3) / `DB_UNREACHABLE` (exit 4). `./fsoctl.sh migrate`
runs this as a non-blocking heads-up first. Add `--require-current` to make a
pending upgrade exit non-zero (for scripted gates).

## Verify (before/after changes)

```bash
docker compose run --rm --no-deps api python -m pytest \
  tests/test_api_v42_contract.py tests/test_api_health.py \
  tests/test_api_system_ops.py tests/test_operations_scripts.py -q
docker compose run --rm --no-deps api python -m pytest tests/integration/test_db_migrations.py -q  # migrations
docker compose run --rm --no-deps web npm run build
docker compose --profile e2e run --rm e2e npm run test:visual                                      # visual gate
```

> Phase 1/146 will surface the worker job queue (queued/running/done/error) and a
> retry affordance in the cockpit so most of "Recover" becomes one click.
