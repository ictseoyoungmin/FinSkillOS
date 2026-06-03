# FinSkillOS Roadmap (2026-06-03)

Phased roadmap from the external review. Goal ordering: **close Phase 0–2
(stabilize → operate → trust the data) before adding new analysis features.**
Hard constraint throughout: descriptive evidence-to-judgment only — never
buy/sell/order/price-direction output.

Slice numbers here are the **actual** sequence continuing from 144 (the review's
139–180 numbering was notional). Live queue + status: `.devmd/CURRENT_STATE.md`.
History: `.devmd/COMPLETED_SLICES.md`.

---

## Phase 0 — Stabilization / regression prevention — ✅ DONE (slices 139–144)
The review's Phase-0 items were already delivered:
- Date-drift test cleanup → **139** (Control Room freshness seeded relative to now).
- CURRENT_STATE split / completed-slice ledger → **144** (+ `COMPLETED_SLICES.md`).
- Migration authoring checklist + dialect guard → **140** (memory) + **138** (the
  `batch_alter_table` fix that prompted it).
- Runtime-settings audit / rollback review → **143** (surface updatedAt/updatedBy;
  confirmed per-key revert + strict validation).
- Worker-queue failure-recovery contract → **142** (`WORKER_QUEUE_AND_API_SPEC.md`).

## Phase 1 — Daily operating loop (ACTIVE)
Make the worker / refresh / System Ops / collection-control surface a loop an
operator can run every day and *understand* (queued / running / done / error /
stale).
- **145 Daily Operations Runbook** — `docs/OPERATIONS_RUNBOOK.md`: start/stop,
  refresh, read state, recover, backup, the daily flow + state vocabulary.
- **146 Worker Queue Visibility / Recovery UI** — surface individual `worker_jobs`
  (queued/running/done/error) in System Ops + a retry/re-enqueue affordance for a
  failed job.
- **147 Refresh Result Explanation UX** — show what the last cycle did (per-type
  succeeded/failed/written + scope) and why a tab is stale/partial.
- **148 Provider Failure / Retry / Backoff Policy** — implement the retry/backoff
  the S7 docs flagged as a gap; bounded attempts, surfaced in worker status.
- **149 Runtime Settings Change History** — full per-change history + one-click
  revert (S5 surfaced last-change metadata only).
- **150 Collection Control Operator Copy Polish** — continue S6: folder-scope vs
  global wording across the tab; empty/disabled honesty.

## Phase 2 — Data trust / provider resilience
Make "why is the data in this state" transparent now that real providers are default.
- **Provider Health Dashboard** — last success / last failure / reason / affected
  tickers per provider, in System Ops.
- **Market Data Provenance Audit** — source/dedup/provenance per bar (extends
  same-day source dedup + indicator backing-bar guard).
- **Indicator / Bar Invariant Dashboard** — every snapshot has a backing bar, etc.
- **News / Event Feed Coverage Diagnostics**.
- **Data Repair / Quarantine Protocols** — safe System Ops cleanup of bad rows.

## Phase 3 — Portfolio / journal real-use input
Reduce input mistakes; reconcile account ↔ journal ↔ snapshot.
- Portfolio manual-entry UX · CSV import/export · position reconciliation view ·
  trade CSV import · Trade Memory review-workflow polish · journal templates.

## Phase 4 — Interpretation engine (still evidence-to-judgment)
Link evidence across tabs.
- Regime explanation v2 · cross-tab evidence graph · risk-guard driver attribution ·
  event/news/position linkage scoring · portfolio constraint summary v2 · weekly
  evidence report.

## Phase 5 — Personal deployment / packaging
- Local release profile · one-command bootstrap (`make` / `fsoctl.sh`) · backup-
  restore drill UX · upgrade/migration safety check · local data-dir policy ·
  versioned release notes.

## Phase 6 — Optional automation / reports / alerts (after core is stable)
- Daily/weekly reports · event-week briefing · worker notification hook · optional
  Telegram adapter · **on-demand LLM explanation boundary** (LLM only narrates
  evidence / reflection prompts — never judgment or trade direction).

---

## Near-term execution order (next ~6 slices)
Phase 1, in order: **145** runbook → **146** worker queue UI → **147** refresh
explanation → **148** retry/backoff → **149** settings history → **150** collection
copy. Then Phase 2 (provider health → provenance). Adjust as findings warrant.
