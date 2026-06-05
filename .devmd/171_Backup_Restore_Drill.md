# 171 — Backup-restore Drill UX (Phase 5)

**Status:** Done. A backup is only trustworthy once verified — this adds an
automated dump-integrity check and a documented full restore drill.

## Implemented

### `scripts/backup_verify.py`
- `verify(path)` checks a `pg_dump` plain-SQL backup is restorable *before* you
  rely on it: non-trivial size, ends with pg_dump's completion marker (catches
  truncated dumps), and declares every core table (`accounts`,
  `portfolio_snapshots`, `positions`, `trades`, `market_bars`,
  `alembic_version`). Read-only — never touches a live DB. Status `OK` (exit 0) /
  `SUSPECT` (exit 3, truncated / empty / missing tables) / `MISSING` (exit 4).
  `--json`, `--min-bytes`, `--help`.

### `fsoctl.sh`
- New `drill` command: back up to `backups/`, then run `backup_verify.py` against
  the dump (in the api container with `./backups` mounted).

### Docs
- `docs/OPERATIONS_RUNBOOK.md` "Backup-restore drill" subsection: the automated
  `drill` + a documented **full drill** (restore the dump into a throwaway
  `finskillos_drill` database, sanity-check, drop) so a restore is proven without
  risking live data.

## Tests (`tests/test_operations_scripts.py`, +4 · `--help` contract +1)
- a synthetic complete dump → `OK`; a dump without the completion marker →
  `SUSPECT` (truncated); a dump missing `alembic_version` → `SUSPECT` with the
  table flagged; a missing file → `MISSING`. The script is in the operations
  `--help` contract.

## Verification
- Offline: operations pytest PASS; ruff clean; manual CLI runs (`--help`,
  missing-file exit 4); `bash -n fsoctl.sh`.
- Docker (rebuilt api image): operations pytest + ruff.

## Notes
- No app / schema change. The dump verifier is offline pure-Python (no DB needed),
  so it's deterministically testable with synthetic dumps. Next: 172 Local
  data-dir policy / release profile.
