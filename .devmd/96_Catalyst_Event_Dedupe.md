# 96 — Catalyst Watch Event De-duplication (read model)

Date: 2026-05-30

## Goal

The live Catalyst Watch "Upcoming Events" table showed the same event repeated
(e.g. "Probe Tentative" × 4). Title is the catalyst identity key — ingestion
(`seed_sample_events` / `refresh_events`) is idempotent by title — but the
`events` table has **no unique constraint**, so legacy / externally inserted
duplicate-title rows accumulate in the DB and surfaced as repeated rows. They
also inflated the event-risk guard's upcoming-event count (Slice 89). Duplicates
must never surface.

## Root cause

- `create_event` has no title guard and there is no DB-level uniqueness, so
  duplicate-title rows can exist (the live local Postgres had `Probe Tentative`
  × 4 from prior probing/test pollution — "Probe" is not in the codebase).
- The read path (`EventService.list_upcoming`) returned every row, so Catalyst
  Watch, the Control Room catalyst rail, and the event-risk guard all saw the
  duplicates.

## Implemented

- `EventService.list_upcoming` now de-duplicates by title (keeping the earliest
  occurrence) **before** applying `limit`. Because Catalyst Watch
  (`build_event_radar_view_model`), the Control Room rail, and the event-risk
  guard (`RiskGuardService._build_event_risk_summary`) all read through this one
  method, the fix propagates everywhere from a single point.
- `_dedupe_events_by_title` helper.

## Notes

- A DB unique constraint on title was intentionally **not** added: it would have
  to delete existing rows in a migration and would make `create_event` raise on
  any duplicate. The read-model dedup tolerates any source of duplicates and
  never shows them — the more robust, lower-risk fix.
- The four legacy `Probe Tentative` rows remain in the local Postgres but are
  now collapsed to one on read; they can be removed with a targeted `DELETE`
  if desired (not done automatically — it is the operator's data).

## Tests added

- `tests/test_event_dedup.py`:
  - `list_upcoming` collapses duplicate titles to one;
  - dedupe respects `limit` (counts unique events);
  - `build_event_radar_view_model` shows no duplicate rows.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_event_dedup.py
  tests/test_event_radar.py tests/test_api_event_radar.py
  tests/test_risk_guard_service.py -q` ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check finskillos/services/event_service.py
  tests/test_event_dedup.py` ✅ All checks passed
- `docker compose run --rm api python -m pytest tests/test_event_dedup.py
  tests/test_api_event_radar.py -q` ✅ passed
- Recreated the `api` container so the live Catalyst Watch shows de-duplicated
  rows immediately.

## Known issues

- None. (Optional follow-up: a one-time live-DB cleanup of the legacy
  `Probe Tentative` rows.)
