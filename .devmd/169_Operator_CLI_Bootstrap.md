# 169 — One-command Bootstrap CLI (`fsoctl.sh`) (Phase 5)

**Status:** Done. Opens Phase 5 (personal deployment / packaging).

A single discoverable entrypoint over `docker compose` for the operator workflow
that was previously a list of raw commands in the runbook. Operator tooling only
— it never trades; the product stays descriptive.

## Implemented

### `fsoctl.sh` (repo root, executable)
- **Lifecycle:** `setup` (build → DB → migrate → seed → start), `build`,
  `up`/`start`, `down`/`stop` (keeps the DB volume), `restart [svc]`, `status`,
  `logs [svc]`.
- **Data / ops:** `migrate`, `seed` (idempotent), `refresh` (one
  `refresh_worker.py --once` cycle), `backup [path]` (→ `scripts/backup_postgres.sh`),
  `restore <file> …` (→ `scripts/restore_postgres.sh`, passes args through; the
  destructive `--confirm-restore` is required by the underlying script, never
  auto-supplied).
- **Verification:** `verify` rebuilds the app images first, then runs the Docker
  test gate (pytest + ruff + web build). `build` / `verify` rebuild because the
  app services bake their source at build time (the Slice 158–164 stale-image
  lesson, now encoded in the tool).
- `help` / unknown-command usage; `set -euo pipefail`; runs from the repo root
  regardless of `cwd`.

### Docs
- `docs/OPERATIONS_RUNBOOK.md` gains an "Operator CLI" section mapping each
  wrapper to the raw compose command it runs.

## Tests (`tests/test_operations_scripts.py`, +2 / extended)
- `fsoctl.sh` parses as bash (`bash -n`); `help` lists the core commands
  (setup/build/up/down/backup/restore/verify); an unknown command exits non-zero.

## Verification
- Offline: operations-scripts pytest PASS; ruff clean; `bash -n` + manual
  `./fsoctl.sh help` + unknown-command exit-2 checks.
- Docker (rebuilt images): operations + v42 + health + system-ops pytest + ruff.

## Notes
- No app code / migration / frontend change (ops tooling + docs + test only).
- Next: 170 Upgrade / migration safety check (preflight alembic head vs DB,
  wired into `fsoctl.sh`).
