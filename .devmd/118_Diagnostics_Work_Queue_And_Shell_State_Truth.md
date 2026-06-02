# 118 — Diagnostics Work Queue And Shell State Truth

Date: 2026-06-02

## Goal

Turn the full-cockpit diagnostic findings into an active numbered work queue,
clear completed historical queue items out of the active list, and fix the first
trust issues found by the audit.

## Implemented

- **Diagnostics ledger** — added `.devmd/PROJECT_DIAGNOSTICS.md` as the
  cross-tab diagnostic record. It captures the initial static findings, the
  full-scroll visual audit, artifact paths, and verification commands.
- **Full-scroll diagnostic spec** — added
  `frontend/e2e/diagnostics/full-scroll-diagnostics.spec.ts`, which captures
  each routed tab through the OS workspace scroll container and records JSON
  metrics plus PNG screenshots under
  `frontend/test-results/diagnostics/full-scroll/`.
- **Work Queue reset** — rewrote `.devmd/CURRENT_STATE.md` Work Queue so active
  work is ordered by diagnostic IDs D-001 through D-010. Completed legacy queue
  entries are no longer repeated in the active queue.
- **D-001 CORS mutation-method contract** — `api/main.py` now allows `PUT` and
  `DELETE` CORS preflight for already-exposed Trade Memory and Symbol Lab
  mutation routes. The app description now names the current safe mutation
  boundary: System Ops protocols, watchlist organization, and Trade Memory
  journal records.
- **D-002 / D-006 shell DB-state truth** — `OsTopTray` now receives
  `/api/system-status` DB state from `OsShell` and renders `DB · LIVE` or
  `DB · MISSING` with matching tone instead of a hard-coded live pill.

## Tests

- `tests/test_api_health.py` covers CORS preflight for existing frontend
  mutation methods.
- `frontend/e2e/db-unavailable.spec.ts` covers both shell DB states:
  unavailable (`DB · MISSING`, danger tone, banner visible) and live
  (`DB · LIVE`, success tone, no banner).
- Full-scroll diagnostics cover all 10 routed tabs for console/page errors,
  horizontal overflow, and lower-page capture artifacts.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build api
docker compose -f docker-compose.yml run --rm api python -m ruff check api/main.py tests/test_api_health.py
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_health.py -q
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/db-unavailable.spec.ts --project=chromium --workers=1
```

Results:

- API image build: passed.
- Ruff (`api/main.py`, `tests/test_api_health.py`): passed.
- Focused API pytest (`tests/test_api_health.py`): 5 passed.
- Web image build: passed.
- Frontend production build/type validation: passed.
- Focused Playwright DB unavailable suite: 2 passed.

## Known Issues

- D-003 frontend live-failure parity remains open for non-Market/Analysis tabs.
- D-004 through D-010 remain queued in `.devmd/CURRENT_STATE.md`.
