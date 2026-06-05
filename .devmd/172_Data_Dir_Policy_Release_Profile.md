# 172 — Local Data-dir Policy / Release Profile (Phase 5)

**Status:** Done. Two packaging concerns: where local state lives, and a stable
local-release way to run the cockpit.

## Implemented

### Local release profile
- `docker-compose.yml` gains a `web-release` service (profile `release`) building
  the frontend `runtime` stage (the existing nginx static-serve target that no
  service used) on `:8080`, with `VITE_API_BASE_URL=/api` baked and the nginx
  `/api`→`api:8000` proxy + SPA fallback. Opt-in / explicit so it never collides
  with the dev `web` (`:5173`) on the default `docker compose up`.
- `fsoctl.sh release` (build + start) / `release-down`.

### Local data-dir policy
- `scripts/data_dir_report.py` — `build_report()` reports the host data dirs
  (`DATA_DIR` / `CACHE_DIR` / `EXPORT_DIR` / `BACKUP_DIR`, env-overridable, with
  existence + file count + bytes), the `.env` presence, the `postgres_data`
  volume note, and the policy line. `--json` / `--help`. Read-only, filesystem-only.
- `fsoctl.sh info` runs it.
- `.env.example` documents `BACKUP_DIR` + the "Postgres lives in the
  `postgres_data` volume; never `down -v`" policy.

### Docs
- `docs/OPERATIONS_RUNBOOK.md`: "Local data-dir policy" table + "Local release
  profile" section; `web-release` added to the services table.

## Tests (`tests/test_operations_scripts.py`, +2 · `--help` contract +1)
- `build_report` lists the four core directories with usage facts and the
  `postgres_data` / `down -v` policy; absent dirs / `.env` are marked absent.
- `data_dir_report.py` added to the `--help` contract.

## Verification
- Offline: operations pytest PASS; ruff clean; `bash -n fsoctl.sh`; manual
  `./fsoctl.sh info` + `--help`.
- Docker: `docker compose --profile release config` valid; `web-release` image
  builds (nginx runtime stage); operations pytest + ruff on the rebuilt api.

## Notes
- No app / schema change. Reuses the pre-existing nginx `runtime` Dockerfile
  stage. Next: 173 Versioned release notes / CHANGELOG (closes Phase 5).
