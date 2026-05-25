# 19 — Restore and System Status Hardening

Status: `DONE`
Date: `2026-05-25`

## Goal

Apply the useful operations feedback after Slices 14–18:

1. Make Postgres restore semantics strict enough for an existing local DB.
2. Separate DB-backed source state from partial/missing data freshness in
   `/api/system-status`.

## Implementation Notes

- `backup_postgres.sh` now emits `pg_dump --clean --if-exists` output.
- `restore_postgres.sh` now performs a confirmed clean restore:
  - stops API/web/debug-admin;
  - drops and recreates the `public` schema;
  - replays the backup with `ON_ERROR_STOP=1`;
  - restarts API/web.
- `/api/system-status` keeps `source=live` when the DB is reachable, even
  if some datasets are stale or missing.
- `/api/system-status` adds `dataCompleteness`:

```text
complete  all tracked freshness timestamps exist
partial   DB is live but at least one tracked dataset is stale/missing
missing   DB is unavailable
```

- System Ops and the global status bar render the new completeness label.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_health.py tests/test_operations_scripts.py -q  # 10 passed
python3 -m ruff check api/routes/health.py tests/test_api_health.py tests/test_operations_scripts.py  # passed
bash -n scripts/backup_postgres.sh scripts/restore_postgres.sh  # passed
docker compose up -d --build api web  # passed
docker compose --profile e2e build e2e  # passed
docker compose --profile e2e run --rm e2e npm run build  # passed
docker compose --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts  # 9 passed
docker compose --profile e2e run --rm e2e npm run test:visual  # 31 passed
```

## Completion

- Restore is clean by default after explicit confirmation.
- Status source and completeness no longer encode two concepts in one field.
- UI shows DB/source/freshness/completeness without exposing execution controls.
