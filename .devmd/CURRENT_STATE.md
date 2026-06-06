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
168  Weekly Evidence Report (Phase 4)
169  Operator CLI / Bootstrap (fsoctl.sh) (Phase 5)
170  Upgrade / Migration Safety Check (Phase 5)
171  Backup-restore Drill UX (Phase 5)
172  Local Data-dir Policy / Release Profile (Phase 5)
173  Versioned Release Notes / CHANGELOG (Phase 5)
174  Scheduled Daily/Weekly Reports (Phase 6)
175  Event-Week Briefing (Phase 6)
176  Worker Notification Hook (Phase 6)
177  Optional Telegram Notification Adapter (Phase 6)
178  On-demand LLM Explanation Boundary (Phase 6)
179  Real-Data Audit + Integrity Guard (v3 Phase 7)
180  Data Authenticity Contract (OriginTag) (v3 Phase 7)
181  Shared Panel Density Pass (v3 Phase 8)
182  Eliminate Layout Void — Evidence Tabs (v3 Phase 8)
183  Use Horizontal Space — Mission/Risk/Catalyst (v3 Phase 8)
184  System Ops History Density (v3 Phase 8)
185  Reusable Pagination for Long Lists (v3 Phase 8)
186  Agent Tool Contract (v3 Phase 9)
187  LLM Provider Abstraction (v3 Phase 10)
188  Ops LLM Provider Switcher (v3 Phase 10)
189  Agent Ingestion Parser + Preview (v3 Phase 11)
190  Agent Paste-Import UI (v3 Phase 11)
191  Agent Chat Backend + Local-LLM Wiring (v3 Phase 11)
192  Agent Chat Widget (v3 Phase 11)
193  Chat Widget Mockup Parity + Image/Vision (v3 Phase 11)
194  Gemini Multi-turn + Vision (v3 Phase 11)
195  LLM-Assisted Free-Form Ingestion (v3 Phase 11)
196  Chat Widget Wider + Resizable + Polish (v3 Phase 11)
197  Fix Over-Aggressive Chat Boundary (v3 Phase 11)
198  Trades-Paste Ingestion (v3 Phase 11)
199  Watchlist via Chat (v3 Phase 11)
200  Brokerage Read-Only Extension Boundary (v3 Phase 12)
201  Self-Review Polish (guard/watchlist/widget) (v3)
202  Agent Read Scope (grounded chat + read tools) (v3)
203  Screen Interpretation (capture → vision) (v3)
204  Loosen Agent Prompt + Expand State Context (v3)
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

### Phase roadmap — `docs/ROADMAP.md` (v2.1) · `docs/v3/` (v3, next)
**v2.1 Phases 0–6 COMPLETE (slices ≤178).** Next arc — agent-operated, real-data
cockpit — planned in [`docs/v3/`](../docs/v3/README.md): Phase 7 real-data
integrity · 8 layout redesign · 9 agent tool contract · 10 LLM provider switching
(Ops) · 11 agent ingestion (paste/screenshot → dry-run → confirm → DB) · 12
brokerage/execution boundary (deferred). **Phase 7–8 ACTIVE** (user: "phase7-8 진행").
- [x] **179 Real-data audit + integrity guard** (v3) — audited the
  seed-from-fixture live builders; fixed a real leak (system-ops live
  `generatedAt` was the fixture sentinel) + `tests/test_real_data_integrity.py`
  guards all seed-from-fixture routes. Doc: `docs/v3/AUDIT_179_real_data.md`.
- [x] **180 Data authenticity contract** (v3) — shared `OriginTag`
  (live/derived/sample/empty) chip; reference usage on Mission Control's derived
  weight % (live-gated → fixture baseline unchanged).
- [x] **181 Shared panel density pass** (v3 Phase 8) — tightened the shared
  `Panel` chrome (head/body padding + gap), densifying all 10 tabs evenly
  ("전체 탭 균등"). **Drifts all `@visual` baselines — user regenerates** via
  `npm run test:visual:update` (decided 2026-06-05).
- [x] **182 Eliminate layout void — evidence tabs** (v3 Phase 8) — the mid-page
  void is column-height imbalance (tall rail vs short chart/center + full-width
  trailing sections pushed down). Flowed the trailing Interpretation/Watchpoints
  into the **shorter** column on Control Room (center), Market Kernel + Symbol Lab
  (chart main), Analysis Workspace (side rail). Drifts those 4 `@visual`
  baselines — user regenerates.
- [ ] Next: remaining 6 tabs (Mission, Risk, News, Catalyst, Trade Memory, Ops —
  different structures; **best after viewing the 4 evidence tabs**, since the work
  is blind) + Phase-7 honesty roll-out (`OriginTag` derived/empty).

Phase 0 (stabilization) DONE via 139–144. **Phase 1 — daily operating loop — DONE
via 145–150. Phase 2 — data trust / provider resilience — DONE via 151–155.
Phase 3 — portfolio / journal real-use input — DONE via 157–162** (reconciliation,
manual entry CRUD, portfolio + trade CSV import/export, weekly-review navigation,
journal templates / review prompts). **Phase 4 — interpretation engine — DONE via
163–168** (risk-guard attribution, regime explanation v2, event/news/position
linkage, portfolio constraint summary v2, cross-tab evidence graph, weekly
evidence report). Next: **Phase 5 — personal deployment / packaging**.

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

#### Phase 4 — interpretation engine — DONE (163–168)
Link evidence across tabs (descriptive only). Read-model / additive — no
mutations. All six surfaced as live-gated additions so the fixture visual
baselines are unchanged (no Playwright regen).
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
- [x] **168 Weekly Evidence Report** (slice 168) — `GET …/weekly-evidence-report`
  assembles a cross-tab markdown report (regime + portfolio + catalysts + trade
  review) via `api/weekly_report.py`, forbidden-wording scanned;
  `WeeklyEvidenceReportPanel` (build / copy / download). Live-gated.
  **Phase 4 complete (163–168).**

#### Phase 5 — personal deployment / packaging — DONE (169–173)
Local release ergonomics: one-command bootstrap, backup/restore drill, migration
safety, data-dir policy, versioned release notes. Mostly ops tooling + docs.
- [x] **169 Operator CLI / Bootstrap** (slice 169) — `fsoctl.sh` one entrypoint
  over docker compose (setup/build/up/down/status/logs/migrate/seed/refresh/
  backup/restore/verify); `verify`+`build` rebuild app images first (baked-image
  lesson). Runbook "Operator CLI" section; ops-test coverage.
- [x] **170 Upgrade / migration safety check** (slice 170) —
  `scripts/migration_safety_check.py` (DB revision vs code head:
  UP_TO_DATE/PENDING/UNINITIALISED/UNKNOWN_REVISION(exit 3)/DB_UNREACHABLE);
  `fsoctl.sh check` + non-blocking preflight in `migrate`. Runbook section.
- [x] **171 Backup-restore drill UX** (slice 171) — `scripts/backup_verify.py`
  (dump integrity: completion marker + core tables, OK/SUSPECT/MISSING) +
  `fsoctl.sh drill` (backup → verify); runbook full-drill (restore into a
  throwaway DB) procedure.
- [x] **172 Local data-dir policy / release profile** (slice 172) — `web-release`
  compose service (profile `release`, nginx static serve :8080) + `fsoctl.sh
  release`/`release-down`; `scripts/data_dir_report.py` + `fsoctl.sh info` +
  `.env.example` BACKUP_DIR/policy; runbook data-dir + release sections.
- [x] **173 Versioned release notes / CHANGELOG** (slice 173) — `CHANGELOG.md`
  (phase-versioned v0.0–v0.5) + `scripts/release_notes.py` (parse `NN — Title`
  commits for a git range) + `fsoctl.sh release-notes`. **Phase 5 complete
  (169–173).**

#### Phase 6 — optional automation / reports / alerts — DONE (174–178)
Additive, gated (default off), offline-safe, descriptive-only.
- [x] **174 Scheduled daily/weekly reports** (slice 174) — `build_daily_brief_markdown`
  / `build_report_markdown` + `scripts/generate_report.py` (--period daily|weekly
  → `data/exports/report_<period>_<date>.md`) + `fsoctl.sh report`. Descriptive,
  wording-scanned.
- [x] **175 Event-week briefing** (slice 175) — `build_event_week_briefing_markdown`
  (catalysts in the next 7d, sorted, with risk score + held-ticker linkage +
  holdings-exposure rollup); `report event-week` period. Descriptive.
- [x] **176 Worker notification hook** (slice 176) — `finskillos/notifications.py`
  (`Notification` / `Notifier` / `NullNotifier` / `LogNotifier` / `build_notifier`
  via `FINSKILLOS_NOTIFY_SINK`); `run_cycle` emits on DONE/ERROR (guarded). The
  seam for 177.
- [x] **177 Optional Telegram adapter** (slice 177) — `TelegramNotifier`
  (injectable sender, stdlib urllib, swallows errors) behind `build_notifier`'s
  `telegram` sink; off unless `FINSKILLOS_NOTIFY_SINK=telegram` + token/chat id
  set (else log fallback). Offline-tested.
- [x] **178 On-demand LLM explanation boundary** (slice 178) —
  `finskillos/llm_explanation.py` (`ExplanationRequest`/`narrate`/`EchoExplainer`;
  output forbidden-wording guard → `ExplanationBoundaryError` so a narrator can
  never emit judgment/direction) + `scripts/explain.py`. Offline echo default.
  **Phase 6 complete (174–178). ROADMAP Phases 0–6 all delivered.**

### Standing open (env-blocked)
- [ ] **Playwright visual baseline regen** — W-4 tab + S5 audit line drift
  `system-ops.png`; needs browser binaries (unavailable here). Run
  `npm run test:e2e -- --update-snapshots` where Playwright browsers exist.

## Next actions
1. Phase 1 in order (145 → 150), then Phase 2.
2. Keep contracts (live/fixture/state copy, runtime-settings ↔ worker payload,
   folder-scope semantics) aligned; run the SQLite alembic smoke on any migration.
