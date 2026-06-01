# Current State — FinSkillOS v2.1 / v4.2 Cockpit

Updated: 2026-05-30

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
63     Control Room State Band Coherence
64     Catalyst Watch Manual Event UX Removal
65     Analysis Workspace DB Read Model Promotion
66     Control Room DB Read Model Promotion
67     Catalyst Watch Backend Mutation Boundary Cleanup
68     Analysis Workspace Coverage Ergonomics
69     Control Room Live Rail Composition
70     System Ops Event Ingestion Hardening
71     Market Structure Coverage Vocabulary
72     Control Room Rail Freshness Detail
73     System Ops Protocol Result Ergonomics
74     Symbol Lab Market Kernel Coverage Parity
75     Control Room Freshness Staleness Thresholds
76     System Ops Protocol Result API Detail Normalization
77     Symbol Lab Coverage Threshold Polish
78     Control Room Freshness Threshold Configuration
79     System Ops Protocol History Evidence Density
80     Reduce DB-Reachable Fixture Fallback (Live-Empty / Live-Error)
81     Refresh Stale v4.2 Fixture-First Contract List
82     Explicit DB-Unavailable State for the Offline Path
83     Market Kernel Coverage Copy Parity with Symbol Lab
84     State Vocabulary / Data Source Contract Doc (+ refresh stale doc 12)
85     System Ops Protocol History Samples in Fixture Mode
86     db-unavailable Distinct State (global banner)
87     get_session_scope DB-outage vs config-bug hardening
88     Frontend Live-Fetch Failure Pill (Market Kernel / Analysis)
89     Event Risk Guard Live Wiring
90     Docker Env-State Test Audit (deterministic run ordering)
91     Shared api/timeutil (dedup _as_utc / _iso)
92     Shared Live-Error Helper + Copy (api/live_state)
93     Event Calendar Provider Adapter (+ EventService.refresh_events)
94     System Ops Event Refresh Protocol
95     CSV Event Calendar Adapter (operator-curated provider)
96     Catalyst Watch Event De-duplication (read model)
97     Market Kernel Live Event Overlay
98     Market Kernel Multi-Timeframe Query
99     Trade Memory Entry Edit / Delete / CSV Export (API)
100    Trade Memory Entry Edit / Delete / Export (UI)
101    Market Bar Same-Day Source Dedup (read model)
102    Market Kernel Indicator Backing-Bar Guard
103    Remove Unused PlaceholderPage (P3 cleanup)
104    LineChart Crosshair Readout + SVG Accessibility
105    Control Room Freshness Env → Operator Watchpoints
106    Control Room State-Band Density
107    Vendor HTTP Event Calendar Provider
108    State-Band Density Parity (Analysis/Symbol/Market Kernel)
109    RegimeStateVector Honest Values (real regime evidence)
110    Market Kernel Indicator Grid Density
111    Real-Data Market Refresh Default (kill mock sawtooth)
112    Worker Auto-Start Orchestration + Test DB Isolation
113    Postgres Worker Job Queue (request-driven worker)
114    System Ops Refresh Enqueues Jobs (request path)
115    Reachable-Empty → Live(-empty) Guard + Sample Cleanup
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
- Control Room now exposes a `dataState` API contract and renders a compact
  overview-source/evidence-coverage/market-tape/linked-module state band, so
  its fixture-first summary does not imply DB-backed parity with promoted
  product tabs.
- Catalyst Watch no longer exposes manual event registration in the React UI.
  The former form has been replaced with read-only event catalog evidence.
- Analysis Workspace `/api/analysis-workspace` now promotes to the DB-backed
  Index Lab read model when a DB session is reachable, reads stored bars,
  indicators, and regime context without provider calls, and keeps
  `X-FSO-Use-Fixture: 1` as the deterministic fixture path.
- Control Room `/api/control-room` now promotes to a DB-backed operating
  overview when a DB session is reachable, composing live mission, portfolio,
  regime, and risk-guard context while marking non-promoted overview rails as
  partial in `dataState`.
- Catalyst Watch `/api/event-radar` is now read-only at the product route
  boundary. Manual-event and Event Radar seed POST routes were removed, the
  `manualEntryRules` contract was dropped, and event seeding remains under
  System Ops.
- Analysis Workspace now distinguishes complete, partial, sparse, and empty
  universe coverage in its API contract, exposes ranked-tape readiness and
  missing-row previews, and renders those cues in the state band.
- Control Room now composes live overview rails from stored market bars,
  Catalyst Watch events, active symbol subscriptions, mission state, and guard
  evidence when those DB rows exist. Missing rails are explicit in `dataState`
  rather than hard-coded as fixture partials.
- System Ops now labels deterministic event catalog ingestion as the dedicated
  System Ops boundary, removes stale manual-upsert copy, reports
  `boundary=system_ops` in seed results, and has a DB-backed regression proving
  event rows remain uncertain-date statuses across OK/NOOP runs.
- Market Kernel now shares Analysis Workspace's coverage vocabulary by exposing
  `coverageLevel`, `evidenceCoveragePercent`, and `missingSummary` in
  `dataState`, while preserving chart/indicator status fields for compatibility.
- Control Room now exposes per-rail freshness detail in `dataState`, including
  latest market, catalyst, and watchlist timestamps plus a compact freshness
  note rendered in the state band.
- System Ops protocol results now render structured detail strings as compact
  evidence chips, separating run timing from created counts, date-status
  summaries, and operational boundary markers.
- Symbol Lab now shares Market Kernel's coverage vocabulary by exposing
  `coverageLevel`, `evidenceCoveragePercent`, and `missingSummary` in
  `dataState`, and its state band now emphasizes coverage rather than only
  chart status.
- Control Room now classifies market, catalyst, watchlist, and aggregate rail
  freshness as `FRESH`, `STALE`, or `MISSING`, so the overview no longer infers
  freshness from timestamp presence alone.
- System Ops protocol results now expose `detailEvidence` key/value rows in
  the API contract while preserving the legacy `detail` string for audit and
  DB-history compatibility.
- Symbol Lab now grades sparse/partial coverage copy quantitatively, reporting
  stored bars against a named indicator-warmup threshold (e.g. "12 of 20 stored
  bars; 8 more complete the indicator window") instead of a binary
  "fewer than 20 stored bars" string.
- Control Room market/watchlist staleness thresholds are now an explicit
  settings contract (`FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS` base plus
  per-rail overrides) instead of a hard-coded three-day constant. The active
  policy is surfaced in `dataState` and the rail freshness note.
- System Ops history now renders each recent protocol run's structured
  `detailEvidence` as compact chips (falling back to parsing the legacy
  `detail` string), sharing one derivation path with the result card.
- Risk Firewall, Mission Control, News Intelligence, and Trade Memory no longer
  fall back to fixture content when a DB session is reachable: missing rows
  (e.g. no account) return an explicit `source="live"` empty state and runtime
  errors return an explicit `source="live"` error state (200, exception class
  name only — never a stack trace or fixture sample). The `use_fixture` opt-in
  and the fully-offline `session is None` fixture paths are unchanged.
- The cross-tab v4.2 contract test now matches the all-promoted reality: a
  DB-state-independent structural check (no header) plus deterministic fixture
  anchor checks (forced `X-FSO-Use-Fixture`), with the fixture-override check
  covering all ten tabs. The stale `fixture-first` list/test was removed.
- The fully-offline (`session is None`) path now labels every tab's per-tab DB
  indicator `MISSING` via a shared `mark_db_unavailable` helper instead of
  claiming `db="LIVE"`. The explicit `X-FSO-Use-Fixture` demo override keeps
  `db="LIVE"`, so a DB outage and an intentional fixture stay distinguishable.
- Market Kernel and Symbol Lab now share one `api/coverage.py` helper for the
  `coverageLevel` / `evidenceCoveragePercent` / `missingSummary` vocabulary, so
  Market Kernel's sparse/partial copy is graded identically to Symbol Lab
  (e.g. "1 of 20 stored bars; 19 more complete the indicator window"); only the
  COMPLETE line keeps a per-tab domain label.
- The state model is now pinned in `docs/v2_1/13_State_Vocabulary_And_Data_Source_Contract.md`
  (fixture / live / live-empty / live-error / db-unavailable, the per-field
  contract, thresholds, and which test enforces each). The stale
  `docs/v2_1/12_Live_Adapter_Boundary.md` boundary table and test rule were
  refreshed to the all-promoted reality.
- System Ops fixture mode now ships a deterministic sample protocol-run history
  (`sample_protocol_runs()`), so the Slice-79 history evidence chips are visible
  in fixture / visual mode without a populated audit log. Forced fixture stays
  deterministic; offline falls back to the samples; the live path stays honest
  (real runs, empty if none). System Ops visual baseline regenerated.
- Market Kernel now overlays live Catalyst Watch events relevant to the selected
  ticker (ticker-linked or market-wide macro, de-duped via Slice 96, tone from
  the event-risk label, capped at 6) instead of a hard-coded empty overlay, and
  its 1D/1W/1M selector is now wired end to end: the API takes a `timeframe`
  query (`1d`/`1wk`/`1mo` + aliases, unsupported → `1d`), reads bars + indicators
  for that timeframe, and reflects it in `header.timeframe`; the React selector
  carries the timeframe in the query key and refetches. Read-only — an
  unstored timeframe shows the explicit MISSING state. Visual baseline unchanged.
- Trade Memory entries can now be edited, deleted, and exported, not just
  appended. The API gained `PUT`/`DELETE /trade-memory/entries/{id}` (same
  forbidden-wording guard + structured JSON result as POST; missing row →
  REJECTED, never a 500) and `GET /trade-memory/export.csv` (deterministic,
  descriptive CSV of the recent entries, works in every snapshot mode). The
  route also dedups its POST/PUT input build, snapshot resolution, and result
  mapping into shared helpers. Frontend edit/delete/export UI is Slice 100.
- The Trade Memory cockpit now surfaces that seam: the Recent Entries table
  shows Edit / Delete actions (live mode only — sample fixture rows stay
  read-only), the journal form switches into an edit mode that PUTs instead of
  appends, and an always-available "Export entries (CSV)" link downloads the
  snapshot. The trade-memory visual baseline was regenerated for the new
  controls; the structural contract test and full visual suite stay green.
- Market Kernel charts no longer sawtooth from mixed-source bars. A mock seed
  bar (00:00 UTC) and a real yfinance bar (04:00 UTC) could share a calendar day
  without colliding on the `(ticker, timeframe, bar_time)` key, so the chart
  plotted both divergent series. `MarketRepository.list_bars` now collapses
  daily-or-coarser bars to one per calendar day (real source over `mock`, then
  latest), leaving intraday untouched; every `len(bars)` coverage number follows.
  The superseded mock seed (941 rows, zero mock-only pairs) was deleted from the
  live DB under user authorization, so the header's latest reverts to the real
  last trading day.
- The Indicator Snapshot panel can no longer lead the chart. `indicator_snapshots`
  held the same mock-derived rows, so the route's latest-by-time pick surfaced a
  phantom 2026-05-31 snapshot. The market_kernel route now only trusts a snapshot
  with a backing (deduped) bar; the 770 orphaned snapshots were deleted under the
  same authorization, restoring the "every snapshot has a backing bar" invariant.
  NVDA's panel reverts to the real 2026-05-29 values (RSI 46.30 / EMA20 228.06).
- The market-refresh default is now real data (`yahoo`), not `mock`: the worker
  and the System Ops `refresh-market-data` route default to yfinance, and `mock`
  is explicit opt-in. The mock adapter had been re-seeding synthetic bars on
  non-trading days (which the same-day dedup can't remove), re-creating the
  chart sawtooth; defaulting to real data + re-cleaning the junk (1911 mock bars
  + 103 orphan indicators) fixes it at the source. Tests stay offline via an
  autouse conftest fixture forcing the mock adapter.
- The shared `LineChart` (Market Kernel + Control Room) is now interactive and
  accessible: hover or arrow-key a crosshair to read the stored value at a point
  (crosshair + per-series dots + tooltip), with an `aria-live` readout and a
  visually-hidden data table for screen readers (SVG itself is `aria-hidden`
  behind an enriched `role="img"` wrapper). At rest the render is unchanged; four
  text-dense baselines (control-room/risk-firewall/mission-control/news-intel)
  were refreshed for unrelated font-raster drift, not chart content.
- Control Room operator watchpoints now propagate the configured freshness
  policy: when the market / watchlist / catalyst rail is STALE, a watchpoint
  cites the exact `FINSKILLOS_CONTROL_ROOM_*_STALE_AFTER_DAYS` threshold it was
  judged against plus refresh guidance. FRESH/MISSING rails add nothing; the
  fixture/visual path is unchanged.
- Catalyst Watch can now ingest a real vendor feed: `HttpEventCalendarAdapter`
  (env-gated `FINSKILLOS_EVENT_CALENDAR_ADAPTER=http` + `..._URL`) fetches a
  vendor-agnostic JSON calendar over HTTP behind the existing adapter boundary,
  so the read models / event-risk guard are untouched. Offline-testable via an
  injected transport (the default `httpx` path is never exercised in the suite);
  fetch/decode/shape errors raise `EventCalendarFetchError` and a refresh
  surfaces a structured ERROR. Completes the mock → csv → http provider ladder.
```

## Validation Baseline

Use these focused Docker checks before touching the v4.2 cockpit surface:

```bash
docker compose -f docker-compose.yml run --rm --no-deps api pytest \
  tests/test_api_v42_contract.py \
  tests/test_api_health.py \
  tests/test_api_system_ops.py \
  tests/test_operations_scripts.py \
  -q

docker compose -f docker-compose.yml run --rm --no-deps api ruff check \
  api/routes/health.py \
  api/dependencies.py \
  tests/test_api_health.py \
  tests/test_operations_scripts.py \
  tests/test_api_v42_contract.py

docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml --profile e2e run --rm e2e npm run test:visual
```

All development and verification for this workspace should run through Docker.

## Work Queue

Active, importance-ordered queue (derived from
`.devmd/TAB_REVIEW_AND_BACKLOG.md`). Work top-down; mark `[x]` and append the
slice number when done, then commit. `[ ]` = pending, `[~]` = in progress.

### P1 — correctness / trust
- _All P1 items complete (Slices 86–90); the full Docker suite is green._
- [x] **96 Catalyst event de-duplication** (spotted in the live UI, prioritized):
  `EventService.list_upcoming` de-dupes by title, so duplicate-title rows never
  surface in Catalyst Watch / Control Room rail / event-risk guard. Verified live
  (upcoming 16 → 13, "Probe Tentative" 4 → 1).

### P2 — shared refactor
- _Complete (Slices 91–92): shared `api/timeutil.py` + `api/live_state.py`._

### P2 — tab features
- **Catalyst Watch live event calendar provider** (L) — _done (offline + curated)_:
  - [x] **93** event-calendar adapter boundary (`BaseEventCalendarAdapter` +
    `MockEventCalendarAdapter`) + `EventService.refresh_events`.
  - [x] **94** System Ops `refresh_events` protocol (card + handler + frontend +
    env-gated adapter selection).
  - [x] **95** `CsvEventCalendarAdapter` (operator-curated calendar, env-gated
    `FINSKILLOS_EVENT_CALENDAR_ADAPTER=csv`).
  - [x] **107** vendor HTTP calendar provider (`HttpEventCalendarAdapter`,
    env-gated `FINSKILLOS_EVENT_CALENDAR_ADAPTER=http` + `..._URL`). Offline-
    testable via an injected transport + `tests/fixtures/events/vendor_calendar.json`;
    vendor-agnostic JSON contract, errors raise `EventCalendarFetchError`.

### P0 — orchestration / live freshness (2026-06-01)
Goal: `docker compose up` runs web+api+worker+db together; the worker keeps the
dashboard fresh from **real** data (no mock junk, no duplication), driven by a
Postgres job queue (request) + an interval.
- [x] **111** real-data market refresh default (`yahoo`); mock opt-in only;
  re-cleaned the re-seeded mock bars + orphan indicators. _Kills the sawtooth at
  the source._
- [x] **112** auto-start orchestration + test DB isolation — `worker` out of its
  profile (starts with `up`), a one-shot `migrate` service (`alembic upgrade
  head`) gates api+worker, and an autouse conftest fixture stops tests writing to
  the production DB (the deeper recurring-junk root cause). Monotonic audit
  `created_at` removes the `seed_sample_events` ordering flake.
- [x] **113** Postgres `worker_jobs` queue (table + `0013` migration + repo) —
  the worker is queue-driven: idles, drains claimed jobs (`FOR UPDATE SKIP
  LOCKED`) each poll tick, enqueues a dedup-safe `refresh_all` on start +
  interval. Idempotent enqueue + upsert = no duplication. Live-proven on `up`.
- [x] **114** System Ops refresh protocols (market/news/indicators) enqueue a
  worker job (`QUEUED`, idempotent, `requested_by=system_ops`) instead of running
  synchronously; cockpit renders QUEUED. Live-proven. Spec:
  `docs/WORKER_QUEUE_AND_API_SPEC.md` (living doc).
- [x] **115** fixture → MISSING audit — confirmed every tab already returns
  live(-empty) (not fixture) on a reachable-empty DB, locked by a 9-tab guard
  test; cleaned the seeded sample portfolio + events from the live DB so
  Mission/Risk/Catalyst show MISSING until real data exists (real market/news
  kept). _P0 orchestration arc 111–115 complete._

### P3 — UI/UX polish (batch)
- [x] **103** remove unused `frontend/src/pages/PlaceholderPage.tsx` (dead shell;
  all 10 routes are real v4.2 pages).
- [x] **104** chart crosshair/tooltip + SVG accessibility — shared `LineChart`
  gains a hover/keyboard value readout (crosshair + dots + tooltip), an
  `aria-live` readout, and a visually-hidden data table; SVG is `aria-hidden`
  behind an enriched `role="img"` wrapper.
- [x] **105** Control Room freshness env propagation to operator notes — a STALE
  market/watchlist/catalyst rail now adds an operator watchpoint citing the
  configured `..._STALE_AFTER_DAYS` threshold + refresh guidance.
- [x] **106** state-band density — Control Room data-state band tightened
  (smaller padding/gap/min-width) and its detail wraps to 2 lines instead of a
  single-line ellipsis. _Original P3 batch complete._

### P3b — density / visual-efficiency (queued from the 2026-05-31 UI survey)
Importance-ordered. Each is a bounded, offline-verifiable slice; the only
visual risk is the per-tab screenshot baseline (regen the changed tab).
- [ ] **Chart axis-label thinning** (highest visual-efficiency win) —
  _deferred per user (2026-06-01)._ `LineChart` axis labels render every point
  (`labels.map`), so a 255-bar daily chart shows an unreadable crammed strip.
  Show ~6–8 evenly-spaced labels (first/last + interior, deterministic) and keep
  the full set in the visually-hidden data table (Slice 104). Affects Market
  Kernel + Control Room tape; regen those two baselines.
- [x] **108 State-band density parity** — applied the Slice-106 treatment
  (tighter tiles + 2-line detail clamp) to the Analysis Workspace / Symbol Lab /
  Market Kernel data-state bands. Sub-threshold, no baseline regen.
- [x] **109 RegimeStateVector honest values** — replaced the fabricated
  trend/RSI/vol/macro/events vector with real regime evidence (decision mode,
  confidence band, and the rule-derived positive/risk factors) via a new
  `OperatingState.state_vector` API field; honest empty state when no regime.
- [x] **110 Indicator snapshot grid density** — tightened the Market Kernel
  indicator grid (gap/min-width) and scoped a denser `.fso-metric` override to
  that grid only (shared metric untouched). Sub-threshold, no baseline regen.

_P3b density batch (108–110) complete; only axis-label thinning remains, deferred._

### Done (this queue)
- [x] **86 db-unavailable distinct state** — global "DB unavailable" banner
  (`OsDbUnavailableBanner`) keyed on system-status `dbStatus="MISSING"`, so
  offline sample shape is never read as live data. Visual baselines unaffected.
- [x] **87 `get_session_scope` error vs config** — only a real DB-availability
  failure (`SQLAlchemyError`/missing driver) yields the db-unavailable state and
  it is logged; config errors propagate; route errors after yield surface
  normally instead of being swallowed.
- [x] **88 frontend live-fetch failure pill** — Market Kernel / Analysis
  Workspace no longer swallow fetch errors into a silent fixture; they render
  the fixture shape with an explicit "Live data unavailable" `StatusPill`.
  (Other seven tabs share the pattern — follow-up.)
- [x] **89 event risk guard live wiring** — `EVENT_PLACEHOLDER_GUARD` now reports
  live Catalyst Watch exposure (`EventRiskSummary` from EventService +
  EventRiskService), staying INFO-only so the WARN/FAIL ladder is unchanged.
- [x] **90 Docker env-state test audit** — full Docker suite swept; the lone
  remaining failure was an unstable run-ordering bug (same-second `ran_at` +
  second-precision `created_at`), fixed with a microsecond `created_at` default.
  Full Docker suite now green.
- [x] **91 shared `api/timeutil.py`** — dedup `_as_utc`/`_iso` across six routes
  into `to_utc` / `iso`; no behaviour change, contract unit-tested.
- [x] **92 shared live-error helper/copy** — `api/live_state.py` centralises
  `exc_detail` + the two shared live-error sentences used by the four Slice-80
  builders; byte-identical responses.
- [x] **93 event-calendar provider adapter** — `BaseEventCalendarAdapter` +
  deterministic `MockEventCalendarAdapter` + `EventService.refresh_events`
  (idempotent), establishing the Catalyst Watch ingestion boundary.
- [x] **94 System Ops event refresh protocol** — `POST /system-ops/refresh-events`
  + protocol card ingest the calendar via the adapter (offline-safe mock,
  env-gated for a future real provider); idempotent OK/NOOP.
- [x] **95 CSV event calendar adapter** — `CsvEventCalendarAdapter` for an
  operator-curated calendar file (`FINSKILLOS_EVENT_CALENDAR_ADAPTER=csv`);
  offline-safe, idempotent, structured ERROR on misconfig.
