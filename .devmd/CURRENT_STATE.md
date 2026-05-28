# Current State — FinSkillOS v2.1 / v4.2 Cockpit

Updated: 2026-05-28

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
40     News Impact Sentiment / Risk Scoring
41     Watchlist Folder Driven Refresh Controls
42     Worker Status Dashboard
43     Worker Status Tab / Command Drawer
44     Mission Control Capital Map DB Coherence
45     System Ops Data Source State Clarity
46     System Ops Health / Freshness Polish
47     System Ops Live Evidence Copy Coherence
48     Worker Cadence Supervision
49     Trade Memory DB Read Model
50     Trade Memory Live State Polish
51     Trade Memory Journal Mutation UX
52     Trade Memory Form Ergonomics
53     Mission Control State Hardening
54     News Intelligence Source Coverage
55     News Intelligence Manual Article Removal
56     Symbol Lab Data State Hardening
57     Mission Control Evidence Density
58     Catalyst Watch Source Date Confidence
59     Market Kernel Data State Hardening
60     Risk Firewall Guard Evidence Density
61     Catalyst Watch DB Read Model Promotion
62     Analysis Workspace State Hardening
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
- Symbol Lab chart data now revalidates provider rows when stale mock tails
  are detected, treats `1mo` as monthly candles and `1y` as annual candles,
  and renders denser timeframe-aware x-axis labels.
- News ingestion now enriches `news_impacts` with deterministic metadata-only
  sentiment/risk labels. News Intelligence and Symbol Lab also apply the same
  read-time fallback for older rows that still contain `UNKNOWN`.
- System Ops and the lightweight worker now share a folder-aware watchlist
  refresh policy. By default refreshes still include all active subscriptions;
  setting `FINSKILLOS_REFRESH_FOLDER_NAMES` scopes subscription-derived refresh
  tickers to active members of named folders while preserving explicit/default
  baseline tickers.
- The lightweight worker now persists completed cycle summaries to
  `worker_cycle_runs`; System Ops exposes and renders a Worker Status panel
  with latest market/news/indicator sub-status and refresh scope metadata.
- Worker Status now lives in its own System Ops tab. The command affordance is
  icon-first beside the global tab rail and opens as a drawer.
- Mission Control's live capital map now reads the DB-backed portfolio exposure
  map coherently instead of falling back to fixture-only copy.
- System Ops live pages now align health, data-source, evidence, and conflict
  copy around the DB-backed state. Fixture-forced responses remain explicit.
- Worker Status now supervises cadence from `worker_cycle_runs`, reporting
  fresh/stale/error/missing cadence and expected next-cycle timing.
- Trade Memory GET routes now read the live DB-backed Slice-12 reflection
  model when a DB session is available; fixture mode remains explicit through
  `X-FSO-Use-Fixture: 1`.
- The React Trade Memory page now shows a source/state band that distinguishes
  deterministic fixture samples, live DB-backed stored entries, and live empty
  journal state.
- The React Trade Memory journal form now refreshes the live read model after a
  successful save, so stored entries appear without a manual reload.
- The React Trade Memory journal form is grouped by journal intent, defaults
  the date to today, exposes compact required/tag/side state, blocks incomplete
  submissions, and includes a reset action for repeated local journaling.
- Mission Control now exposes a compact source/DB/exposure state band, keeps
  sector and theme exposure panels visible even when live rows are absent, and
  has an API regression proving reachable empty DB state remains live rather
  than silently falling back to fixture copy.
- News Intelligence now exposes source coverage as an API contract, renders a
  compact provider/article/coverage band, keeps impact-map empty states
  testable, and no longer exposes manual news registration.
- Symbol Lab now exposes `dataState` as an API contract and renders a compact
  source/chart/indicator/logo/subscription state band, while E2E checks are
  live-aware instead of relying on fixed fixture shortcut or position rows.
- Mission Control now uses a compact evidence digest instead of four large
  lower evidence panels, keeping verdict, lead driver, uncertainty, and review
  watchpoints visible without expanding the page with repeated narrative.
- Catalyst Watch now exposes a `dataState` API contract and renders a compact
  calendar source/date-confidence band, so a live DB session is not confused
  with a promoted live event-calendar read model.
- Market Kernel now exposes a `dataState` API contract and renders a compact
  source/chart/indicator/event state band, aligned with Symbol Lab's
  live/fixture/missing-data language.
- Risk Firewall now exposes a `dataState` API contract and renders a compact
  evaluation/risk/guard/alert-write state band. Live active-alert rows now
  serialize through the canonical camelCase schema.
- Catalyst Watch `/api/event-radar` now promotes to a live DB-backed read
  model when a DB session is reachable, returns explicit live-empty state when
  no upcoming event rows exist, and filters unsafe external linked-news copy
  instead of letting provider headlines break the read model.
- Analysis Workspace now exposes a `dataState` API contract and renders a
  compact universe-source/coverage/ranked-tape/regime state band, aligning
  Index Lab copy with the rest of the evidence tabs.
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

1. Control Room state-band coherence
   - Recheck the overview grid after individual tabs gained explicit
     `dataState` contracts, so summary cards do not imply fixture/live states
     that differ from the underlying tabs.

2. Catalyst Watch manual event UX removal/replacement
   - Decide whether manual event entry should remain now that the tab has a
     DB-backed read model, or replace it with read-only event catalog evidence.

3. Analysis Workspace DB read-model promotion
   - Promote `/api/analysis-workspace` from fixture-first Index Lab snapshot
     to DB-backed stored bars/indicators once universe storage is wired.
