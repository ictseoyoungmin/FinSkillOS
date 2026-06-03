# 144 — Split CURRENT_STATE → Dashboard + History (S3)

**Status:** Done. Docs reorganization only.

Per the 2026-06-03 review (S3): `CURRENT_STATE.md` had grown to ~660 lines,
doubling as a live dashboard *and* a full historical log, so an agent could lose
the active signal in the history.

## Changes
- **New `.devmd/COMPLETED_SLICES.md`** (history) — the numbered completed-slices
  list (13.11…144) + the long per-slice prose narrative moved out of
  CURRENT_STATE.
- **`.devmd/CURRENT_STATE.md` is now a lean dashboard (~135 lines)** — architecture,
  product boundary, a **Key references** block (point to COMPLETED_SLICES, the
  state-vocabulary doc, the worker/API spec, collection-control spec, and
  workflow_and_memory instead of re-describing them), the **last ~13 slices**, the
  Validation Baseline (+ the migration SQLite-smoke reminder), and an **active**
  Work Queue (recently-closed summary + the genuinely open items: visual-baseline
  regen; noted follow-ups for runtime-settings history/revert and worker
  retry/backoff).

## Why this is safe
- No authoritative content lost: the verbose Work-Queue checklists (W/AW/S/P) were
  duplicative of the per-slice `.devmd/<NN>_*.md` notes + the numbered list, which
  both remain. `CURRENT_STATE.md` stays the authority for *live* state (queue +
  next actions); `COMPLETED_SLICES.md` is the authority for *history*.

## Verification
- Docs-only; no code/test change. Confirmed line counts (CURRENT_STATE 661→135,
  COMPLETED_SLICES 431) and no dangling references to the moved sections.

This closes the S-series stabilization backlog (S1–S7). Remaining open item across
the whole queue: the Playwright visual-baseline regen (blocked — needs browsers).
