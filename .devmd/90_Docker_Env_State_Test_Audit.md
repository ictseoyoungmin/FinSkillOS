# 90 — Docker Env-State Test Audit + Deterministic Run Ordering

Date: 2026-05-30

## Goal

Slices 81 and 83 each fixed a stale "no-header test assumes fixture values but
gets live against a seeded DB" failure. This slice audits the **whole** suite in
Docker against the seeded local postgres and closes the last remaining failure.

## Audit result

Running the full suite in Docker against the seeded postgres surfaced exactly
**one** failure:
`tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
(the test that had been deselected as "env-state" since Slices 77–89).

Root cause — **not** env-state, but a real **non-deterministic ordering** bug:

- `api/routes/system_ops.py::_now_iso` stores protocol-run `ran_at` at **second
  precision** (`isoformat(timespec="seconds")`).
- `SystemOpsProtocolRun.created_at` used `server_default=func.now()`, also second
  precision on sqlite.
- The test POSTs `seed-sample-events` twice in rapid succession (same second), so
  both `ran_at` **and** `created_at` tie. `list_recent` orders by
  `ran_at DESC, created_at DESC`, but with both keys equal the DB returns rows in
  insertion order, so `recentProtocolRuns[0]` was the **first** (events_seeded)
  run instead of the **second** (noop) run the test expects. It only passed when
  the two POSTs happened to straddle a second boundary.

## Implemented

- `finskillos/db/models/system_ops.py`: added a microsecond-precision ORM-side
  `default=_utcnow` to the `created_at` column of **both** audit tables
  (`SystemOpsProtocolRun`, `WorkerCycleRun`). `server_default=func.now()` is kept
  for raw inserts. Now two rows written within the same second still order
  deterministically by insertion time, so `list_recent` (and the System Ops
  history) returns the newest run first.
- No Alembic migration needed: only the ORM-side insert default changed; the
  column DDL (and `server_default`) is unchanged.

## Tests

- Re-enabled the previously-deselected test; it now passes deterministically
  (ran 3× locally, all green) and in the full Docker suite.
- No test changes were required — the fix is in the model, not the assertion.

## Notes

- The audit confirms there are no remaining stale fixture-assumption failures in
  the suite; the lone failure was an ordering bug, now fixed at the source.
- This also makes the System Ops recent-run history (Slice 79/85) deterministic
  for same-second runs.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest
  tests/test_api_system_ops.py::test_seed_sample_events_... -q` ✅ 3× passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` (no deselect) ✅ all passed
- `docker compose run --rm api python -m pytest tests -q` (seeded postgres)
  ✅ full suite green (0 failures)
- `docker compose run --rm --no-deps api python -m ruff check
  finskillos/db/models/system_ops.py` ✅ All checks passed

## Known issues

- None remaining in the test suite.
