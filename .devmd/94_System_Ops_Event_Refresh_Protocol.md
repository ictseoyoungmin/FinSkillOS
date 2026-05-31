# 94 — System Ops Event Refresh Protocol

Date: 2026-05-30

## Goal

Make the Slice-93 event calendar provider usable from the cockpit — the second
part of the "Catalyst Watch live event calendar provider" item, mirroring Slice
23 (System Ops Market Refresh) for events.

## Implemented

- `api/routes/system_ops.py`:
  - `POST /api/system-ops/refresh-events` → `_run_protocol(key="refresh_events")`.
  - `_invoke_refresh_events(session)` ingests via `EventService.refresh_events`
    using `_event_calendar_adapter()` (offline-safe `MockEventCalendarAdapter`
    by default; `FINSKILLOS_EVENT_CALENDAR_ADAPTER` selects a future real
    provider, mirroring the market-refresh adapter selection). OK / NOOP result
    with `events_ingested` / `noop_existing` detail + `boundary=system_ops`.
- `api/schemas/system_ops.py`: `refresh_events` added to `ProtocolKey`.
- `api/fixtures/system_ops.py`: new "Refresh event calendar" protocol card.
- Frontend: `ProtocolKey` type, `PROTOCOL_PATHS` endpoint map, and the React
  mock fixture card (`systemOps.fixture.ts`) gained `refresh_events`.

## Tests

- `tests/test_api_system_ops.py`:
  - `_PROTOCOL_KEYS` / `_POST_ENDPOINTS` extended with `refresh_events` (so the
    catalogue, structured-JSON, and safe-wording loops cover it).
  - `test_refresh_events_protocol_ingests_calendar` — live DB: first run OK with
    `events_ingested` evidence, second run NOOP (idempotent), ingested rows keep
    uncertain TENTATIVE / WINDOW statuses (never CONFIRMED).
- System Ops visual baseline regenerated (8 protocol cards).

## Notes

- Reuses the generic `_run_protocol` wrapper and the existing React
  `ProtocolCardItem` (cards render from the payload), so only data + the endpoint
  map changed — no new UI component.
- Descriptive wording only; the new card/result pass the System Ops
  forbidden-wording checks.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_system_ops.py -q`
  ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check api/routes/system_ops.py api/fixtures/system_ops.py
  api/schemas/system_ops.py tests/test_api_system_ops.py` ✅ All checks passed
- `docker compose run --rm --no-deps web sh -c "npm run build && npm run lint"`
  ✅ build clean · lint 0 errors
- `docker compose --profile e2e run --rm e2e npx playwright test
  e2e/visual/all-tabs.visual.spec.ts -g "system-ops" --update-snapshots` then
  re-run without `--update-snapshots` ✅ baseline green

## Known issues

- Real external calendar provider (env-gated `FINSKILLOS_EVENT_CALENDAR_ADAPTER`)
  remains the final follow-up of the Catalyst calendar item.
