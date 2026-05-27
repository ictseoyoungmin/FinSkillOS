# Current State — FinSkillOS v2.1 / v4.2 Cockpit

Updated: 2026-05-27

## Architecture

FinSkillOS is now a Python domain/service/db core with a FastAPI adapter
and a Vite React v4.2 Evidence-to-Judgment cockpit.

```text
finskillos/       domain, services, DB models, regime, signals, guards
api/              FastAPI read-only adapter + System Ops protocols
frontend/         React/Vite product cockpit
.devmd/           active execution slices and handoff state
docs/v2_1/        source design references
tests/            API, UI, acceptance, regression, operations contracts
```

Streamlit remains available as debug/admin through the compose `app`
profile. It is not the primary product UI.

## Product Boundary

Allowed output:

```text
market state
risk interpretation
portfolio constraints
watchpoints
reflection support
operational protocols
```

Not allowed:

```text
buy/sell recommendations
order placement
brokerage execution
direct trading actions
price-direction commands
```

The FastAPI app is read-only except for idempotent System Ops
operational protocols.

## Current Completed Slices

```text
13.11  React UI Completion Audit + v4.2 Parity Polish
13.12  Arbitrary Symbol Search
13.13  Source-of-Truth Cleanup Before Operations
14     Deployment and Operations
15     System Ops Audit / History Evidence
16     Fixture / Live / Data-Unavailable Labeling
17     Safety Copy Polish
18     Scheduler / Refresh Policy
19     Restore and System Status Hardening
20     Live Adapter Boundary Hardening
21     Risk Firewall DB Read Model
22     Market Provider Adapter
23     System Ops Market Refresh Protocol
24     Market Kernel DB Read Model
25     System Ops Indicator Calculate Protocol
26     Lightweight Refresh Worker
27     Symbol Lab DB Read Model
28     Symbol Identity / Logo Fallback
29     Symbol Subscription and Live Preview
30     Yahoo Provider Diagnostics and Symbol Chart
31     Symbol Candles / Overlays / yfinance Adapter
32     News RSS / Atom Provider Adapter
33     News Feed Configuration / Worker / Status Integration
34     Foldered Symbol Subscriptions / Watchlist Organization
35     Symbol Logo Provider Cache / Shared Ticker Identity
36     Mission Control DB Read Model
37     Portfolio Seed Position Coherence
38     System Ops DB Audit Table
39     Mission Control Live UI Layout
```

Slice 14 is complete:

```text
- /api/system-status freshness and DB status contract implemented.
- React System Ops consumes system-status in its health/freshness panels.
- backup_postgres.sh and restore_postgres.sh added.
- Live compose backup/temporary-DB restore drill verified.
- Docker Playwright visual gate verified: 31 passed.
- System Ops protocol runs are appended to a local JSONL audit log and
  surfaced as recentProtocolRuns.
- The global OS status bar labels snapshot source, DB status, freshness
  stale-count state, read-only mode, and snapshot timestamp on every tab.
- Regime and risk guard copy uses constraint/review language instead of
  action-like reduction, entry, or cash-increase instructions.
- Refresh is manual-first and cron-compatible through scripts for market
  bars, indicators, and regime scans; worker infrastructure remains deferred.
- Postgres restore uses confirmed clean restore semantics, and
  `/api/system-status` separates DB source from data completeness.
- Live DB reachability is separated from fixture-first product tab snapshots;
  `docs/v2_1/12_Live_Adapter_Boundary.md` defines promotion order.
- `/api/risk-firewall` is the first DB-backed product read model when a DB
  session and account exist; fixture fallback remains explicit.
- `scripts/refresh_market_data.py --adapter yahoo` can explicitly fetch live
  ticker bars through the Yahoo Chart API into the existing DB-backed market
  data service. Product market tabs remain fixture-first until promoted.
- System Ops exposes a `refresh_market_data` protocol card. It defaults to
  offline-safe mock refresh and can use Yahoo only through explicit env
  configuration.
- `/api/market-kernel` can read stored DB bars and latest indicator snapshots
  without calling a provider during page rendering.
- System Ops exposes a `calculate_indicators` protocol card. It computes
  descriptive snapshots from stored bars and keeps worker infrastructure
  deferred.
- Docker Compose exposes an optional `worker` profile running
  `scripts/refresh_worker.py`. The worker refreshes market bars, RSS news
  metadata, and descriptive indicators when enabled.
- `/api/symbol-lab` can read stored DB bars, latest indicator snapshots,
  current position context, symbol-linked active alerts, and shared ticker
  logo identity metadata.
- Symbol Lab now exposes `identity` metadata and renders a provider-cache logo
  when `FINSKILLOS_LOGO_DEV_TOKEN` is configured; otherwise it uses the local
  fallback avatar.
- Symbol Lab supports arbitrary ticker subscription toggles. Active
  `symbol_subscriptions` are included in System Ops and worker refresh
  universes; unsubscribe keeps historical bars/indicators intact.
- Symbol Lab renders a close-line chart from API bars, displays recent bars
  newest-first, and reports Yahoo preview failures in missing-data guidance.
- Symbol Lab renders OHLC candles with volume and selectable EMA/Bollinger
  overlays, exposes a timeframe query, and uses `yfinance` at the market
  provider boundary.
- RSS/Atom news metadata can be refreshed by System Ops, scripts, or the
  worker, using explicit feed configuration or subscribed/focus ticker-derived
  Google News RSS queries.
- Symbol subscriptions can be organized into durable folders without changing
  the active refresh universe semantics.
- Symbol Lab and News Intelligence share a DB-backed Logo.dev URL cache with
  local initials fallback. The current seeded cache contains 120 Nasdaq/focus
  ticker logo metadata rows.
- `/api/mission-control` now reads live account goal progress, portfolio
  snapshot, current positions, exposure maps, and active alert context when
  the DB is reachable. `X-FSO-Use-Fixture: 1` still forces the deterministic
  fixture.
- `seed_sample_account` now keeps the default sample account internally
  coherent by creating current positions whose market value plus cash matches
  the initial portfolio snapshot. The local DB's prior snapshot-only seed
  state has been repaired.
- System Ops protocol runs are now persisted in `system_ops_protocol_runs`
  through Alembic `0011_system_ops_protocol_runs`. The API still writes the
  local JSONL sidecar, but `GET /api/system-ops` reads recent runs and
  protocol `lastRunAt` from the DB when reachable.
- Mission Control now uses a compact live-operations layout: narrative,
  source/freshness, portfolio totals, guard count, and goal progress are in
  the first scan band; detailed evidence is moved below the mission state.
```

## Validation Baseline

Use these focused checks before touching the v4.2 cockpit surface:

```bash
python3 -m pytest \
  tests/test_api_v42_contract.py \
  tests/test_api_health.py \
  tests/test_api_system_ops.py \
  tests/test_operations_scripts.py \
  -q

python3 -m ruff check \
  api/routes/health.py \
  api/dependencies.py \
  tests/test_api_health.py \
  tests/test_operations_scripts.py \
  tests/test_api_v42_contract.py

docker compose --profile e2e run --rm e2e npm run build
docker compose --profile e2e run --rm e2e npm run test:visual
```

Host Node may be unreliable in WSL for this workspace; prefer the Docker
e2e image for frontend build and visual checks.

## Next Useful Slices

1. News impact sentiment/risk scoring
   - The RSS provider stores articles and impacts, but many generated impacts
     still show UNKNOWN sentiment/risk. Improve deterministic scoring and
     source confidence before adding broader feed coverage.

2. Watchlist-folder driven refresh controls
   - Let folder organization guide user-facing refresh/filter controls while
     keeping the worker's active subscription universe predictable.

3. Worker status dashboard
   - Summarize worker cycles and protocol freshness using DB audit rows.
