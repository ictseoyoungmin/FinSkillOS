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
132  Collection Control Confirm + Undo (idea U9)
133  Market Kernel Add-to-Folder (idea U1)
134  Per-Folder Refresh Now (idea F3; + VARCHAR(80) scope fix)
135  Regime Context Confidence Unit Fix (AW-1)
136  Worker Recomputes Regime Each Cycle (AW-2)
137  Regime Staleness Surfacing + Coverage Copy (AW-3)
138  SQLite-Compatible 0017 Scope Migration (batch_alter_table)
139  Control Room Freshness Test Date-Drift Fix
140  Capture Review Feedback + Stabilization Queue
141  Collection Refresh Semantics Copy (S6)
142  Worker Failure-Recovery Docs (S7)
143  Runtime Settings Change Audit (S5)
144  Split CURRENT_STATE → COMPLETED_SLICES history (S3)
```

## Validation Baseline

All development and verification run through Docker. Focused checks before
touching the v4.2 cockpit surface:

```bash
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
Phase 0 (stabilization) DONE via 139–144. Now working **Phase 1 — daily operating
loop** (make queued/running/done/error/stale understandable + recoverable).

#### Phase 1 (active)
- [x] **145 Daily Operations Runbook** — `docs/OPERATIONS_RUNBOOK.md` (services,
  first-time setup, daily start/stop, state vocabulary, refresh & collection,
  recover, backup/restore, verify). Commands cross-checked against compose/scripts.
- [ ] **146 Worker Queue Visibility / Recovery UI** — surface individual
  `worker_jobs` (queued/running/done/error) + retry/re-enqueue a failed job.
- [ ] **147 Refresh Result Explanation UX** — show what the last cycle did + why a
  tab is stale/partial.
- [ ] **148 Provider Failure / Retry / Backoff** — implement the S7-flagged gap.
- [ ] **149 Runtime Settings Change History** — full history + one-click revert
  (S5 surfaced last-change only).
- [ ] **150 Collection Control Operator Copy Polish** — continue S6.

#### Later phases (see ROADMAP.md)
Phase 2 data-trust/provider-resilience · Phase 3 portfolio/journal input · Phase 4
interpretation engine · Phase 5 packaging · Phase 6 optional automation/LLM-narration.

### Standing open (env-blocked)
- [ ] **Playwright visual baseline regen** — W-4 tab + S5 audit line drift
  `system-ops.png`; needs browser binaries (unavailable here). Run
  `npm run test:e2e -- --update-snapshots` where Playwright browsers exist.

## Next actions
1. Phase 1 in order (145 → 150), then Phase 2.
2. Keep contracts (live/fixture/state copy, runtime-settings ↔ worker payload,
   folder-scope semantics) aligned; run the SQLite alembic smoke on any migration.
