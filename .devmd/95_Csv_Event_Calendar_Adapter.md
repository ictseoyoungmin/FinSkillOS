# 95 — CSV Event Calendar Adapter (operator-curated provider)

Date: 2026-05-30

## Goal

Final non-vendor piece of the Catalyst Watch live calendar provider. Slice 93/94
added the adapter boundary + a deterministic mock + the System Ops refresh
protocol. This slice adds a second concrete, offline-safe provider — an
operator-curated CSV calendar — mirroring `CsvMarketDataAdapter`. A real vendor
HTTP provider remains an optional future branch; the CSV adapter already lets an
operator ingest a real, curated event calendar without any network dependency.

## Implemented

- `finskillos/data_sources/event_adapter.py`:
  - `CsvEventCalendarAdapter(path)` — reads a curated calendar CSV
    (`title,event_type,date_status,start_date` + optional
    `end_date,source,importance_score,ticker,sector,theme,event_key`), one link
    per row, ISO dates. Missing file → `EventCalendarFetchError`; row values are
    validated downstream by `EventService.create_event`.
  - `_links_from_row` helper builds a single `EventLinkInput` when any link
    column is present.
- `api/routes/system_ops.py::_event_calendar_adapter` now supports
  `FINSKILLOS_EVENT_CALENDAR_ADAPTER=csv` with `FINSKILLOS_EVENT_CALENDAR_CSV`
  (missing path → `ValueError`, surfaced as a structured protocol ERROR), in
  addition to the default `mock`.

## Tests added

- `tests/fixtures/events/calendar_sample.csv` — 3 curated events (TSLA earnings,
  ECB, semiconductor regulation) with ticker / event_key / sector links.
- `tests/test_event_calendar_adapter.py` — CSV parse + links, missing-file error,
  Protocol conformance, `refresh_events` ingest + idempotency from CSV.
- `tests/test_api_system_ops.py` — `refresh_events` protocol with the CSV adapter
  ingests the curated calendar; CSV adapter without a path returns a structured
  `ERROR` (ValueError), not a raw 500.

## Notes

- Offline-safe and deterministic — no network. The protocol/read models are
  unchanged; only the adapter selection gained a branch.
- Curated rows keep the uncertain-status discipline (operator supplies
  WINDOW/TENTATIVE/SPECULATIVE; CONFIRMED still requires a non-seed source via
  `EventService` validation).

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_event_calendar_adapter.py
  tests/test_api_system_ops.py -q` ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check finskillos/data_sources/event_adapter.py
  api/routes/system_ops.py tests/test_event_calendar_adapter.py
  tests/test_api_system_ops.py` ✅ All checks passed
- `docker compose run --rm api python -m pytest tests/test_event_calendar_adapter.py
  tests/test_api_system_ops.py -q` ✅ passed

## Known issues

- A real vendor HTTP calendar provider (env-gated branch) remains an optional
  future addition; mock + CSV cover offline and operator-curated ingestion.
