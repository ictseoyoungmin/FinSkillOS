# 107 — Vendor HTTP Event Calendar Provider

Date: 2026-05-31

## Goal

The last optional Catalyst item: a real vendor HTTP calendar provider behind the
existing `BaseEventCalendarAdapter` boundary (after mock / csv in Slices 93/95),
so Catalyst Watch can ingest a live vendor feed without touching the read models
or event-risk guard. Must stay offline-testable (no network in the suite).

## Implemented

- `finskillos/data_sources/event_adapter.py` — `HttpEventCalendarAdapter`:
  - Vendor-agnostic JSON contract: a JSON array of event objects, or an object
    with an `"events"` array. Per record: `title`, `event_type`, `date_status`,
    `start_date` (ISO), optional `end_date`, `source`, `source_url`,
    `description`, `importance_score`, and either a `links: [{ticker, sector,
    theme, event_key}]` array or top-level `ticker/sector/theme/event_key`.
  - `event_type` / `date_status` are validated downstream by
    `EventService.create_event`, so a vendor `CONFIRMED` row is allowed only
    when it cites a non-seed `source` (the descriptive-only / no-fabricated-fact
    rule still holds). Network, JSON-decode, shape, and bad-date problems raise
    `EventCalendarFetchError` so a refresh fails loudly, never silently ingests
    junk. Empty-title records are skipped.
  - **Offline-safe by injection**: `transport=callable(url) -> str` is injected
    in tests; the default `_http_get` lazily uses `httpx` and is never exercised
    by the suite (`# pragma: no cover`).
- `api/routes/system_ops.py::_event_calendar_adapter` — new `http` branch gated
  by `FINSKILLOS_EVENT_CALENDAR_ADAPTER=http` + `FINSKILLOS_EVENT_CALENDAR_URL`
  (missing URL → `ValueError`, surfaced by the refresh protocol as a structured
  `ERROR`, never a raw 500 / network call).

## Tests

- `tests/test_event_calendar_adapter.py` (7 new) — parse the
  `tests/fixtures/events/vendor_calendar.json` fixture via an injected
  transport: titles + skipped empty record, importance/source mapping, links[]
  vs top-level link fallback, a vendor CONFIRMED+source row accepted, bare-list
  payload, invalid-JSON / bad-start-date raise, protocol conformance, and an
  `EventService.refresh_events` integration (ingest + idempotent).
- `tests/test_api_system_ops.py` (2 new) — the `http` branch builds the adapter
  from env (construction only, no fetch); a missing URL is a structured ERROR.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_event_calendar_adapter.py
  tests/test_api_system_ops.py -q` ✅
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `ruff check` ✅ clean
- Docker pytest (calendar adapter + system ops + v42 contract) ✅

## Known issues

- The default `httpx` transport is intentionally untested (would need network);
  the parsing + selection logic is fully covered offline via injection.
