# 156 — Stale RUNNING Job Reaper (+ lint hygiene)

**Status:** Done. A Phase-0/1/2 review (2026-06-04) finding.

## The bug the review surfaced
During the Phase-2 review the live queue showed a job stuck in `RUNNING` for **~22
hours** (`worker_start`, started 2026-06-03 04:48). When a worker container dies
mid-cycle (the WSL/Docker `exit 255` events happened repeatedly this session), the
job it claimed stays `RUNNING` forever: `claim_next` only picks `QUEUED`, and the
slice-146 Retry button only acts on *terminal* (DONE/ERROR) jobs. So an orphaned
claim had **no recovery path** and skewed the `jobCounts` / Provider-Health view.

## Fix
- **`WorkerJobRepository.reap_stale_running(older_than)`** — marks jobs `RUNNING`
  with `started_at < older_than` as `ERROR` ("worker stopped while the job was
  running (reaped)"). Reaped jobs are terminal → retryable from the cockpit (146).
- **Worker** calls `reap_stale_running_jobs(config)` at the top of every
  `drain_queue`, so any live worker recovers orphaned claims within a poll tick.
  Gated by `FINSKILLOS_WORKER_RUNNING_STALE_SECONDS` (default 1800 = 30 min, 0
  disables) — generous so a genuinely in-progress cycle is never killed. Added to
  the allow-list + `.env.example`.

## Also (review hygiene)
- Whole-tree `ruff check api/ finskillos/ scripts/ tests/` surfaced one pre-existing
  `I001` import-sort in `api/schemas/news_intelligence.py` (last touched slice 55,
  unrelated to Phase 0/1/2 — the per-slice ruff only checks changed files). Fixed;
  the whole tree is now lint-clean.

## Tests
- `tests/test_worker_jobs.py`: two claimed (RUNNING) jobs; backdate one past the
  grace → `reap_stale_running` marks only it ERROR ("reaped"), leaving the fresh
  RUNNING job untouched.

## Verification
- Offline: worker-jobs + ops-scripts + system-ops tests PASS; whole-tree ruff clean;
  full `pytest tests/` suite green (2026-06-04, no date-drift regression).
- Docker: api/worker images + pytest + ruff.
- Live: rebuilt worker reaps the real 22h-stuck job (RUNNING → ERROR), and it then
  becomes retryable in the Job Queue panel.

## Review summary (Phase 0–2)
Tree clean, single alembic head 0018, all new env vars in allow-list + .env.example,
full suite green, all Phase 1/2 endpoints live 200, provider health HEALTHY. The one
real defect found (stuck RUNNING jobs) is fixed here.
