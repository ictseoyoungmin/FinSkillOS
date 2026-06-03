# 138 — SQLite-Compatible 0017 Scope Migration

**Status:** Done. Fixes a dialect bug in the slice-134 migration.

## Root cause
Migration `0017_widen_worker_cycle_scopes` widened the `worker_cycle_runs.*_scope`
columns with `op.alter_column(type_=String(80))`, which emits
`ALTER TABLE … ALTER COLUMN … TYPE …`. **SQLite has no ALTER COLUMN**, so the
alembic-on-SQLite migration smoke test (`tests/integration/test_db_migrations.py`)
failed: `sqlite3.OperationalError: near "ALTER": syntax error`. The slice-134
Docker checks only exercised Postgres, so it slipped through.
See [[feedback_sqlite_dialect_gotchas]] (#5 migration smoke; #6 String length).

## Fix
- Wrap the type change in `op.batch_alter_table("worker_cycle_runs")` (upgrade +
  downgrade). Batch mode is portable: SQLite recreates the table; Postgres issues
  a normal `ALTER`. This is the project's existing pattern (cf. migration 0007).

## Live impact
- None. The live Postgres already has `0017` applied (same revision id, columns
  already `VARCHAR(80)`); alembic won't re-run it, and batch mode is equivalent on
  Postgres for a fresh DB.

## Verification
- Offline: `tests/integration/test_db_migrations.py` (3) PASS; full `pytest tests/`
  suite green; ruff clean.
- Docker: api image migration smoke (SQLite) PASS.
