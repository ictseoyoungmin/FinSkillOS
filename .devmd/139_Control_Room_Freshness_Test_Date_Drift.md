# 139 — Control Room Freshness Test Date-Drift Fix

**Status:** Done.

## Root cause
`test_control_room_promotes_live_overview_rails` seeded market bars at a hard-coded
`2026-05-30` and asserted `marketFreshnessStatus == "FRESH"`. The route judges
freshness against `vm.generated_at` (= today) on a calendar-day basis
(`FRESH if observed_date >= today − stale_after_days`, default 3). Once the
calendar advanced past the window the seed read STALE, so the test failed every
day from ~2026-06-02 on — a date-drift time-bomb (confirmed failing on a clean
tree during slice 134).

## Fix
- Seed **relative to `now`**: the latest bar lands at `now − 1 day` (FRESH for any
  threshold ≥ 1, default 3) and the catalyst event stays upcoming (`now + 2 days`,
  FRESH since events are STALE only when `date < today`). Date-string assertions
  are derived from the computed timestamps (`market_prefix`, `event_date`) instead
  of literals, so the test is stable on any run date.

## Audit
- Swept the suite for the same pattern (FRESH assertion + hard-coded `datetime(2026…)`
  seed). This was the only currently-failing date-drift test; the others
  (analysis-workspace, symbol-lab, etc.) drive freshness from timestamps they
  control or assert non-freshness fields, so they don't rot.

## Verification
- Offline: `tests/test_api_control_room.py` (21) PASS; full `pytest tests/` suite
  green; ruff clean.

## Remaining queue item (separate, blocked)
- Playwright `system-ops.png` visual baseline regen (W-4 added a tab) needs browser
  binaries, unavailable in this environment — still open, run
  `npm run test:e2e -- --update-snapshots` where browsers are available.
