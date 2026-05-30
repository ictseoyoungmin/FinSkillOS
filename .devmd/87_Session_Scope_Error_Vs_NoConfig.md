# 87 — get_session_scope: DB Outage vs Config Bug

Date: 2026-05-30

## Goal

`api/dependencies.py::get_session_scope` wrapped everything in
`except Exception: yield None`, so it masked **all** failures as a DB outage —
including configuration bugs (e.g. an invalid settings value) and route-level
errors thrown back into the generator after `yield session` (a latent
"generator didn't stop" hazard). Narrow the failure handling so only genuine
DB-availability failures become the db-unavailable state, and stop swallowing
the rest silently (the stale TODO at line 27).

## Implemented

- `get_settings()` is now read **outside** the `try`, so a configuration error
  propagates (it is a bug, not a DB outage) instead of being masked as offline.
- The reachability probe (`create_engine` + `SELECT 1`) is wrapped in
  `except (SQLAlchemyError, ImportError)` → `yield None` (db-unavailable). This
  covers connection-refused / unreachable **and** a missing DB driver
  (offline / fixture-only mode without `psycopg`). The failure is logged
  (`logger.warning(..., exc_info=True)`), so it is no longer silent.
- The session is yielded in a **separate** `try/finally` (probe before yield),
  so route-level errors after the yield surface normally (Slice 80 gives product
  routes their own explicit live-error states) instead of being caught and
  turned into a second `yield None` (which previously risked a RuntimeError).
- Replaced the stale 13.7-era TODO with the current contract description.

## Tests added

- `tests/test_dependencies.py`:
  - `test_db_connection_failure_yields_none` — a `SQLAlchemyError` during engine
    creation yields `None` (db-unavailable).
  - `test_config_error_propagates_instead_of_masking_as_offline` — an invalid
    `FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS` raises `ValueError` through the
    context manager instead of becoming a silent fixture fallback.
  - `test_reachable_sqlite_yields_session` — a reachable DB yields a live session.

## Notes

- "Missing driver" is treated as db-unavailable on purpose: in production the
  driver is installed, so this only matters for local/offline fixture-only mode,
  which is exactly the state the original fallback served.
- The user-facing "Live pill while DB is down" symptom was already closed by
  Slices 82 (db=MISSING label) and 86 (global banner); this slice hardens the
  underlying boundary and removes the silent config-error masking.
- No product/route/schema/copy change.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_dependencies.py -q`
  ✅ 3 passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect <known
  env-state system_ops test>` ✅ all passed (no regression)
- `docker compose run --rm api python -m pytest tests/test_dependencies.py
  tests/test_api_v42_contract.py tests/test_api_control_room.py
  tests/test_api_db_unavailable.py` ✅ passed (live + offline paths)
- `docker compose run --rm --no-deps api python -m ruff check api/dependencies.py
  tests/test_dependencies.py` ✅ All checks passed

## Known issues

- The pre-existing env-state `tests/test_api_system_ops.py::test_seed_sample_events_...`
  failure on the local persistent postgres is unrelated.
