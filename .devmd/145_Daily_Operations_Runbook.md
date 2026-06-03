# 145 — Daily Operations Runbook (Phase 1)

**Status:** Done. Docs (`docs/OPERATIONS_RUNBOOK.md`). Opens Phase 1.

The worker / refresh / System Ops / collection-control surface had grown but there
was no single "how do I run this every day" doc. The runbook grounds the daily
operating loop so the subsequent Phase-1 feature slices (worker queue UI, refresh
explanation, retry/backoff) have a defined operator flow to improve.

## Contents
- Services table (postgres/migrate/api/web/worker + app/e2e profiles) with ports;
  cockpit at :5173, API at :8000.
- First-time setup (build → up postgres → migrate → seed → up); daily start/stop/
  status; the daily loop.
- Reading state — the vocabulary (source / db / freshness / coverage) an operator
  must distinguish.
- Refresh & collection — worker live-mode toggle, System Ops protocols
  (queued vs synchronous), Collection Control + per-folder "this folder only"
  refresh, real-vs-mock adapter.
- Recover — failed job / stale regime / idle worker / DB-unavailable.
- Backup/restore (`--confirm-restore`) and the Docker verify commands.

## Accuracy
Commands cross-checked against `docker-compose.yml` (service names, ports,
profiles), `scripts/{backup,restore}_postgres.sh` (the `--confirm-restore` gate),
and `scripts/seed_sample_data.py`. The seed command intentionally omits `--no-deps`
(it needs the DB on the compose network); the offline test commands keep `--no-deps`
(autouse isolation fixture → no DB needed).

## Verification
- Docs-only; no code/test change. A forward pointer notes that 146 will surface the
  job queue + a retry affordance in the cockpit.
