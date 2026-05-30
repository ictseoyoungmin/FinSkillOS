# 85 — System Ops Protocol History Samples in Fixture Mode

Date: 2026-05-30

## Goal

Slice 79 added per-run `detailEvidence` chips to the System Ops history area, but
the default fixture left `recentProtocolRuns` empty (the route read the local
JSONL audit log even in fixture mode, which is empty in a clean env). So the
history evidence chips were invisible in fixture / visual mode. Add a
deterministic sample run history so the chips are visible without a populated
audit log, and regenerate the System Ops visual baseline.

## Implemented

- `api/fixtures/system_ops.py` — new `sample_protocol_runs()` returning three
  deterministic `ProtocolRunRecord`s (calculate_indicators / refresh_market_data
  / seed_sample_events) each with `detailEvidence` key/value rows and
  `source="fixture"`; `system_ops_fixture()` now ships them as
  `recent_protocol_runs`.
- `api/routes/system_ops.py`:
  - Forced fixture (`X-FSO-Use-Fixture`) now keeps the deterministic samples
    instead of reading the local JSONL — so demos and visual baselines are
    deterministic.
  - Offline (`session is None`) prefers real local audit runs and falls back to
    the samples (`_read_recent_protocol_runs() or payload.recent_protocol_runs`).
  - The **live** path is unchanged and stays honest (real DB runs, empty if
    none).
- `frontend/src/mocks/fixtures/systemOps.fixture.ts` — mirrors the three sample
  runs so the React `placeholderData` matches the API.
- `frontend/e2e/visual/all-tabs.visual.spec.ts` — added `recent-protocol-runs`
  to the System Ops required testids (history now always renders in fixture
  mode) and regenerated `system-ops-chromium-linux.png`.

## Tests

- `tests/test_api_system_ops.py::test_fixture_mode_shows_deterministic_protocol_history`
  — forced fixture returns three deterministic runs, each carrying
  `detailEvidence` chips.
- Existing JSONL/DB audit round-trip tests are unaffected (they use the
  no-header offline/live paths; the fallback only triggers on an empty log).
- Regenerated System Ops visual baseline + structural visual test now asserts
  `recent-protocol-runs` is present.

## Notes

- Live mode is intentionally **not** given sample fallback — a live System Ops
  with no stored runs shows an empty history honestly.
- Sample runs are clearly `source="fixture"` records; no fabricated live audit
  history.
- Descriptive-only copy; no execution wording introduced.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_system_ops.py -q`
  ✅ (only the pre-existing env-state `test_seed_sample_events_...` fails on the
  local persistent postgres; unrelated)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect <that test>`
  ✅ all passed
- `docker compose run --rm --no-deps api python -m ruff check
  api/fixtures/system_ops.py api/routes/system_ops.py tests/test_api_system_ops.py`
  ✅ All checks passed
- `docker compose run --rm --no-deps web npm run build` ✅
- `docker compose --profile e2e run --rm e2e npx playwright test
  e2e/visual/all-tabs.visual.spec.ts -g "system-ops" --update-snapshots`
  then re-run without `--update-snapshots` ✅ baseline green

## Known issues

- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure persists on the local persistent postgres and is unrelated to this
  slice.
