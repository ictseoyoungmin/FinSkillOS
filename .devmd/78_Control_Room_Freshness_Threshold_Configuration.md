# 78 — Control Room Freshness Threshold Configuration

Date: 2026-05-30

## Goal

Move the hard-coded three-day Control Room market/watchlist staleness threshold
into an explicit settings contract so operational cadence can vary by
environment (and, when needed, per rail). The previous
`MARKET_RAIL_STALE_AFTER_DAYS = 3` module constant governed both the market and
watchlist freshness classification with no way to tune it without a code edit.

## Implemented

- Added two `Settings` fields in `finskillos/config.py`:
  `control_room_market_stale_after_days` and
  `control_room_watchlist_stale_after_days`.
  - Base env var `FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS` (default `3`)
    applies to both rails.
  - Per-rail overrides `FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS` /
    `FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS` win when set.
  - New `_positive_int(raw, field)` helper validates each value is an integer
    `>= 1`, raising `ValueError` on bad input (mirrors the existing
    `FINSKILLOS_TARGET_VALUE` validation style).
- `api/routes/control_room.py`:
  - Removed the `MARKET_RAIL_STALE_AFTER_DAYS` module constant.
  - `_timestamp_freshness_status` now takes an explicit `stale_after_days`
    argument; the data-state builder reads the per-rail settings and passes the
    market threshold to the market rail and the watchlist threshold to the
    watchlist rail.
  - `_rail_freshness_note` now appends the active policy
    (`stale > 3d`, or `stale > Xd market / Yd watchlist` when they differ).
- `api/schemas/control_room.py`: `ControlRoomDataState` now exposes
  `market_stale_after_days` / `watchlist_stale_after_days` (default `3`) so the
  active policy is an observable contract.
- `frontend/src/features/control-room/types.ts` and the control-room mock
  fixture gained the two fields; the existing state band already renders
  `railFreshnessNote`, which now carries the policy string.
- Documented the new env vars in `.env.example`.

## Tests added

- `tests/test_config.py` (new) — settings contract: default `3` for both rails,
  base env applies to both, per-rail override beats base, non-integer rejected,
  non-positive (`0`) rejected.
- `tests/test_api_control_room.py`
  - Extended the stale-rail regression to assert the default `3` thresholds in
    `dataState`.
  - `test_control_room_freshness_threshold_is_configurable` — a wide base
    threshold reclassifies an otherwise-stale market rail as FRESH and the note
    shows `stale > 3650d`.
  - `test_control_room_freshness_threshold_supports_per_rail_override` — market
    and watchlist thresholds are independently configured, surfaced, and the
    note renders the split policy.

## Notes

- Catalyst freshness keeps its own same-day rule (`_event_freshness_status`);
  this slice only generalizes the timestamp-based market/watchlist rails, which
  were the two governed by the single removed constant.
- The threshold is read from cached settings per request; tests use
  `reset_settings_cache()` around `monkeypatch.setenv` to re-read patched env.
- Copy remains descriptive operational language only — no buy/sell, execution,
  or price-direction wording was introduced.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_control_room.py
  tests/test_config.py -q` ✅ 22 passed (local)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q --deselect
  tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  ✅ all passed (no regression)
- `docker compose -f docker-compose.yml run --rm --no-deps api env
  FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_control_room.py
  tests/test_config.py tests/test_api_v42_contract.py` ✅ passed
- `docker compose -f docker-compose.yml run --rm --no-deps api python -m ruff
  check finskillos/config.py api/routes/control_room.py
  api/schemas/control_room.py tests/test_api_control_room.py tests/test_config.py`
  ✅ All checks passed
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
  ✅ build succeeds (control-room type + fixture changes typecheck)

## Known issues

- The same pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure noted in Slice 77 persists on the local persistent postgres. It is
  unrelated to this slice.
