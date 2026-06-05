# 170 — Upgrade / Migration Safety Check (Phase 5)

**Status:** Done. A preflight that tells the operator whether it's safe to
upgrade / restore — wired into `fsoctl.sh`.

## Implemented

### `scripts/migration_safety_check.py`
- Compares the database's current Alembic revision (`MigrationContext`) against
  the code's migration head (`ScriptDirectory`). `evaluate(database_url)` returns
  a structured status without raising:
  - `UP_TO_DATE` (exit 0) · `PENDING_UPGRADE` (exit 0; count of pending revisions)
    · `UNINITIALISED` (exit 0; fresh DB) · `UNKNOWN_REVISION` (**exit 3** — the DB
    is at a revision the code doesn't know; the code is likely older than the DB,
    a downgrade risk) · `DB_UNREACHABLE` (exit 4).
  - `--require-current` makes `PENDING_UPGRADE` exit 2 (for scripted gates);
    `--json` for machine output; `--database-url` to override; `--help`.

### `fsoctl.sh`
- New `check` command runs the preflight (brings up postgres, runs in the api
  container). `migrate` now runs it as a **non-blocking** heads-up before
  `alembic upgrade head`.

### Docs
- `docs/OPERATIONS_RUNBOOK.md` "Migration safety preflight" section.

## Tests (`tests/integration/test_migration_safety.py`, +5 · operations test +1)
- uninitialised DB → `UNINITIALISED`; a migrated SQLite DB → `UP_TO_DATE`
  (current == head); a foreign `alembic_version` row → `UNKNOWN_REVISION`;
  descriptive `detail` copy. The script is added to the operations `--help`
  contract.

## Verification
- Offline: migration-safety + operations pytest PASS; ruff clean; manual CLI
  runs (uninitialised / up-to-date / `--help`).
- Docker (rebuilt api image): operations + migration-safety + v42 pytest + ruff.

## Notes
- No app schema change. SQLite-friendly (the check reads `alembic_version`, no
  Postgres-only features). Next: 171 Backup-restore drill UX.
