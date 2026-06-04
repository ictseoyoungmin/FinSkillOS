# Current State — FinSkillOS v2.1 / v4.2 Cockpit

Updated: 2026-06-03

> **Dashboard, not a log.** This file is the lean live-state board: architecture,
> recent slices, the active work queue, and next actions. The full per-slice
> history moved to [`COMPLETED_SLICES.md`](COMPLETED_SLICES.md) (slice 144 / S3).
> Per-slice detail: `.devmd/<NN>_*.md`. Workflow/memory:
> `.devmd/workflow_and_memory/`.

## Architecture

FinSkillOS is a Python domain/service/db core with a FastAPI adapter and a Vite
React v4.2 Evidence-to-Judgment cockpit.

```text
finskillos/       domain, services, DB models, regime, signals, guards
api/              FastAPI read-only adapter + System Ops protocols
frontend/         React/Vite product cockpit
.devmd/           active execution slices and handoff state
docs/v2_1/        source design references
tests/            API, UI, acceptance, regression, operations contracts
```

Streamlit remains available as debug/admin through the compose `app` profile. It
is not the primary product UI.

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

The FastAPI app is read-only except for idempotent System Ops operational
protocols.

## Key references (don't re-describe; point here)

- [`COMPLETED_SLICES.md`](COMPLETED_SLICES.md) — full slice history (13.11…).
- `docs/v2_1/13_State_Vocabulary_And_Data_Source_Contract.md` — fixture / live /
  live-empty / live-error / db-unavailable contract + which test enforces each.
- `docs/WORKER_QUEUE_AND_API_SPEC.md` — worker, job queue, failure/recovery,
  regime-recompute coupling, runtime overlay, System Ops protocols.
- `docs/COLLECTION_CONTROL_SPEC.md` / `docs/COLLECTION_CONTROL_IDEAS.md` —
  folder-driven collection control.
- `.devmd/workflow_and_memory/MEMORY.md` — working rules (Docker-only verification,
  migration authoring checklist, SQLite/PG gotchas, slice workflow, descriptive-only).

## Recent slices (full list in COMPLETED_SLICES.md)

```text
145  Daily Operations Runbook (Phase 1)
146  Worker Queue Visibility / Recovery UI (Phase 1)
147  Refresh Result Explanation UX (Phase 1)
148  Provider Failure / Retry / Backoff (Phase 1)
149  Runtime Settings Change History (Phase 1)
150  Collection Control Operator Copy Polish (Phase 1)
151  Provider Health Dashboard (Phase 2)
152  Market Data Provenance Audit (Phase 2)
153  Indicator / Bar Invariant Dashboard (Phase 2)
154  News / Event Feed Coverage Diagnostics (Phase 2)
155  Data Repair Protocol (Phase 2)
156  Stale RUNNING Job Reaper (+ lint hygiene)
157  Position Reconciliation View (Phase 3)
158  Portfolio Manual Entry / Edit (Phase 3)
159  Portfolio CSV Import / Export (Phase 3)
160  Trade Import CSV (Phase 3)
161  Trade Memory Review Workflow Polish (Phase 3)
162  Journal Templates / Review Prompts (Phase 3)
163  Risk-Guard Driver Attribution (Phase 4)
164  Regime Explanation v2 (Phase 4)
165  Event/News/Position Linkage Scoring (Phase 4)
166  Portfolio Constraint Summary v2 (Phase 4)
167  Cross-tab Evidence Graph (Phase 4)
```

## Validation Baseline

All development and verification run through Docker. **The `api` / `web` /
`migrate` / `worker` services are baked images with no source bind-mount, and
`docker compose run` does not rebuild — so you must `docker compose build api web`
*before* the Docker gate or it silently tests stale code (a false-green that bit
slices 158–164 on 2026-06-04; the rebuilt-image gate re-validated them). Iterate
locally (`FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest …` + `npm run build` / `tsc`
/ `ruff` / `eslint`) — that runs the real current code — then rebuild + run the
final Docker gate.** Focused checks before touching the v4.2 cockpit surface:

```bash
docker compose -f docker-compose.yml build api web   # required: refresh baked source
docker compose -f docker-compose.yml run --rm --no-deps api pytest \
  tests/test_api_v42_contract.py tests/test_api_health.py \
  tests/test_api_system_ops.py tests/test_operations_scripts.py -q

docker compose -f docker-compose.yml run --rm --no-deps api ruff check <changed paths>
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml --profile e2e run --rm e2e npm run test:visual
```

Migration slices additionally run the **SQLite alembic smoke**
(`pytest tests/integration/test_db_migrations.py`) — Docker/Postgres green does not
imply SQLite green (slices 134/138). See `workflow_and_memory/feedback_docker_migration_workflow.md`.

## Work Queue

Mark `[~]` while in progress, then `[x]` with the implementation note when done.

### Closed recently (detail in COMPLETED_SLICES.md / .devmd notes)
- **W — Folder-Driven Collection Control** (127–131) + ideas U9/U1/F3 (132–134) — DONE.
- **AW — Analysis Workspace audit** (135/136/137) — DONE (regime confidence unit,
  worker regime recompute, staleness + coverage copy).
- **Suite robustness** (138/139) — DONE (SQLite migration, date-drift test).
- **S — Stabilization** (2026-06-03 review): S1/S2/S4 done; S6 (141), S7 (142),
  S5 (143), S3 (144) done. Backlog detail:
  `workflow_and_memory/project_stabilization_backlog_2026_06_03.md`.
- **P1–P3 diagnostics** (D-001…D-010, slices 118–125) — DONE.

### Phase roadmap — `docs/ROADMAP.md`
Phase 0 (stabilization) DONE via 139–144. **Phase 1 — daily operating loop — DONE
via 145–150. Phase 2 — data trust / provider resilience — DONE via 151–155.
Phase 3 — portfolio / journal real-use input — DONE via 157–162** (reconciliation,
manual entry CRUD, portfolio + trade CSV import/export, weekly-review navigation,
journal templates / review prompts). Next: **Phase 4 — interpretation engine**.

#### Phase 1 — DONE (145–150)
- [x] **145 Daily Operations Runbook** — `docs/OPERATIONS_RUNBOOK.md` (services,
  first-time setup, daily start/stop, state vocabulary, refresh & collection,
  recover, backup/restore, verify). Commands cross-checked against compose/scripts.
- [x] **146 Worker Queue Visibility / Recovery UI** (slice 146) — `workerStatus`
  now exposes `jobCounts` + `recentJobs`; a "Job Queue" panel shows status-colored
  rows + a Retry button; `POST …/worker-jobs/{id}/retry` re-enqueues a terminal job.
- [x] **147 Refresh Result Explanation UX** (slice 147) — cycle records now carry
  counts (bars/articles/snapshots/failures/regime) + a readable `outcome` line,
  shown in the Worker Status hero + trace.
- [x] **148 Provider Failure / Retry / Backoff** (slice 148) — bounded per-ticker
  retry of transient `MarketDataFetchError` with exponential backoff
  (`FINSKILLOS_MARKET_FETCH_RETRIES` / `_BACKOFF_SECONDS`); injectable sleep for
  offline tests. Implements the S7-flagged gap.
- [x] **149 Runtime Settings Change History** (slice 149) — `system_ops_settings_history`
  table (migration 0018), per-key change log in the GET response, a "Change history"
  list + "Reset all to defaults" (`POST …/runtime-settings/reset`).
- [x] **150 Collection Control Operator Copy Polish** (slice 150) — subtitle
  explains the Active-folder + type-flag model ("inactive folder / off type
  collects nothing"); totals relabeled + tooltips; global toggles → "Apply to all
  folders". **Phase 1 complete.**

#### Phase 2 — data trust / provider resilience — DONE (151–155)
- [x] **151 Provider Health Dashboard** (slice 151) — `workerStatus.providerHealth`
  rolled up from recent cycles (status / last-clean / last-failure / affected
  tickers + reason) + a System Ops panel. Market cycle summary now records
  `failedTickers`.
- [x] **152 Market Data Provenance Audit** (slice 152) — `GET …/data-provenance`
  (source distribution + tickers whose newest bar is synthetic) + a "Data
  Provenance" panel. Repo `source_distribution` / `latest_source_by_ticker`.
- [x] **153 Indicator / Bar Invariant Dashboard** (slice 153) — `GET …/data-invariants`
  audits orphan indicator snapshots (no backing bar, the slice-102 invariant) + a
  "Data Invariants" panel. Repo orphan NOT EXISTS query.
- [x] **154 News / Event Feed Coverage Diagnostics** (slice 154) — `GET …/feed-coverage`
  (news + event counts / freshness / sources) + a "Feed Coverage" panel.
- [x] **155 Data Repair Protocol** (slice 155) — `POST …/data-repair` (dry-run →
  `?confirm=true` hard-delete) removes synthetic bars + orphan snapshots (operator-
  confirmed scope); real bars never touched; "Data Repair" panel with preview→confirm.
  **Phase 2 complete.**

#### Phase 3 — portfolio / journal real-use input — DONE (157–162)
- [x] **157 Position Reconciliation View** (slice 157) — Mission Control
  `reconciliation` block (snapshot total vs positions+cash, OK/MISMATCH/NO_BASELINE)
  + a panel line. Read-only opener.
- [x] **158 Portfolio Manual Entry / Edit** (slice 158) — descriptive holdings CRUD
  (`POST`/`PUT`/`DELETE …/positions`, `POST …/clear-positions`,
  `PATCH …/snapshot`) returning the refreshed snapshot; a `PortfolioEditorPanel`
  on Mission Control (table edit/delete + add/edit form + baseline editor +
  "Clear sample"), gated to live+LIVE. Reconciliation updates in place.
- [x] **159 Portfolio CSV Import / Export** (slice 159) — `GET …/positions/export.csv`
  (read-only) + `POST …/import-positions` (dry-run preview → `?confirm=true`
  upsert; CSV tickers add/update, absent holdings kept). Editor CSV section
  (export / paste-or-file / preview adds·updates / apply). Shared
  `parse_portfolio_csv` / `serialize_positions_csv`.
- [x] **160 Trade Import CSV** (slice 160) — `POST …/trade-memory/import`
  (dry-run preview → `?confirm=true`, append-only + atomic: nothing written if any
  row is invalid). `TradeCsvImport` panel (file/paste → preview counts + flagged
  errors → append). Shared `TRADE_CSV_COLUMNS` / `parse_trade_csv`.
- [x] **161 Trade Memory Review Workflow Polish** (slice 161) — weekly-review
  period navigation: `GET …/weekly-review?as_of=YYYY-MM-DD` computes the window
  ending that date; `WeeklyReviewPanel` prev/next/this-week stepper (live-gated)
  drives both the panel and the markdown export. Fixture render unchanged.
- [x] **162 Journal Templates / Review Prompts** (slice 162) — `TradeFormRules`
  gains `entryTemplates` (quick-fill chips that scaffold an entry) + `reviewPrompts`
  (a reflection checklist `ReviewPromptsPanel`). Live-gated; fixture render
  unchanged. **Phase 3 complete (157–162).**

#### Phase 4 — interpretation engine (active)
Link evidence across tabs (descriptive only). Read-model / additive — no
mutations. Slice plan (may adjust): 163 risk-guard driver attribution · 164
regime explanation v2 · 165 event/news/position linkage scoring · 166 portfolio
constraint summary v2 · 167 cross-tab evidence graph · 168 weekly evidence report.
- [x] **163 Risk-Guard Driver Attribution** (slice 163) — `GuardSummaryVM` gains
  optional `attribution` (`GuardDriver{label,value}` from each guard's `evidence`)
  + `watchNext`; Risk Firewall live path populates them; `GuardCard` "Why this
  state?" drilldown. Live-gated by data → fixture/Control Room baselines unchanged.
- [x] **164 Regime Explanation v2** (slice 164) — Analysis Workspace `RegimeContext`
  gains `attribution` (indicator evidence via shared `api/evidence_format`) +
  `confidenceRationale` (band + factor counts, no fabricated thresholds);
  `RegimeContextPanel` renders both. Evidence threaded through the shared
  `RegimeSummary` VM. Live-gated; fixture unchanged.
- [x] **165 Event/News/Position Linkage Scoring** (slice 165) — `EventRiskRow`
  gains `scoreDrivers` (the multiplicative factor breakdown behind
  `eventRiskScore`) + `heldTickers` (affected tickers actually held);
  `EventRiskTable` per-event "Score & linkage" details row, held tags highlighted.
  Live-gated; fixture unchanged.
- [x] **166 Portfolio Constraint Summary v2** (slice 166) — Mission Control
  `constraints` block (single-position limit / cash reserve / drawdown headroom,
  OK/WATCH/BREACH) computed from the real Slice-06 guard constants;
  `ConstraintSummaryPanel`. Live-gated; fixture unchanged.
- [x] **167 Cross-tab Evidence Graph** (slice 167) — Control Room `evidenceGraph`
  (regime/risk/events/portfolio nodes + derived cross-reference links) built from
  the already-assembled VMs; `EvidenceGraphPanel` node grid + link list.
  Live-gated; fixture unchanged.
- [ ] **168 Weekly Evidence Report**.

#### Later phases (see ROADMAP.md)
Phase 5 packaging · Phase 6 optional automation/LLM-narration.

### Standing open (env-blocked)
- [ ] **Playwright visual baseline regen** — W-4 tab + S5 audit line drift
  `system-ops.png`; needs browser binaries (unavailable here). Run
  `npm run test:e2e -- --update-snapshots` where Playwright browsers exist.

## Next actions
1. Phase 1 in order (145 → 150), then Phase 2.
2. Keep contracts (live/fixture/state copy, runtime-settings ↔ worker payload,
   folder-scope semantics) aligned; run the SQLite alembic smoke on any migration.
