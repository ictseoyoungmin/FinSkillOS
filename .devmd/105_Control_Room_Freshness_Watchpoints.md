# 105 — Control Room Freshness Env → Operator Watchpoints

Date: 2026-05-31

## Goal

P3 polish. Slice 78 made the Control Room staleness thresholds a settings
contract (`FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS` + per-rail
`..._MARKET_..` / `..._WATCHLIST_..` overrides), and the data-state exposes the
freshness statuses + the configured day counts. But the operator-facing
**watchpoints** never mentioned freshness, so an operator reading the posture
notes couldn't see that a rail was stale or what policy it was judged against.
Propagate the configured threshold into the watchpoints.

## Implemented (`api/routes/control_room.py`)

- `_freshness_watchpoint_rows(data_state)` — emits an operator watchpoint for
  each rail whose freshness is `STALE`:
  - market → "Market data stale … past the {market_stale_after_days}-day
    freshness window; run a System Ops market refresh …"
  - watchlist → "Watchlist stale … past the {watchlist_stale_after_days}-day
    freshness window; refresh watchlist inputs …"
  - catalyst → "Catalyst window passed … review Catalyst Watch for newer
    events." (event freshness is "older than today", no day threshold)
- `_watchpoints(vm, data_state)` appends those rows after the existing
  read-only / evidence-tab / regime / alert notes. The live builder passes the
  already-computed `payload.data_state`, so the threshold shown is exactly the
  one the rail was judged against (default 3, or any env override).
- FRESH / MISSING rails add nothing. Descriptive only — refresh guidance, no
  execution wording.

No schema or frontend change: the rows flow through the existing
`WatchpointsPanel`. Forced-fixture / visual paths are unchanged (the fixture
watchpoints carry no stale rails), so no baseline regen.

## Tests (`tests/test_api_control_room.py`)

- Extended `test_control_room_classifies_stale_market_and_watchlist_rails`: a
  stale market + watchlist (default 3-day) now surfaces "Market data stale" /
  "Watchlist stale" watchpoints citing the "3-day freshness window".
- New `test_control_room_freshness_watchpoints_cite_configured_threshold`: a
  deterministic unit test of `_freshness_watchpoint_rows` — a STALE market at a
  non-default 9-day threshold cites "9-day", a FRESH watchlist adds nothing and
  its threshold is not cited, and an all-MISSING data-state yields no rows.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_control_room.py -q`
  ✅ (18 passed)
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `ruff check` ✅ clean
- Docker pytest (control room + v42 contract) ✅

## Known issues

- None. Completes the Control Room freshness-env item of the P3 batch.
