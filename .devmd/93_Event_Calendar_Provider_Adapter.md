# 93 — Event Calendar Provider Adapter + EventService.refresh_events

Date: 2026-05-30

## Goal

First bounded slice of the "Catalyst Watch live event calendar provider" item.
Establish the provider boundary for event ingestion — mirroring how market data
went (Slice 22 adapter → Slice 23 System Ops refresh). Currently Catalyst Watch
events come only from the hard-coded Slice-11 `seed_sample_events` catalog. This
slice adds an adapter boundary + a deterministic offline provider so a real
external calendar can later plug in without changing the read models.

## Implemented

- `finskillos/data_sources/event_adapter.py`:
  - `BaseEventCalendarAdapter` (`@runtime_checkable Protocol`) —
    `fetch_events(*, today) -> Sequence[SeededEvent]`.
  - `MockEventCalendarAdapter` — deterministic, offline rolling earnings + macro
    window (NVDA / AAPL earnings, CPI, FOMC) relative to `today`, using only
    uncertain date statuses (TENTATIVE / WINDOW), never CONFIRMED.
  - `EventCalendarFetchError` for future live providers.
- `EventService.refresh_events(adapter, *, today)` — ingests adapter events
  idempotently by title (same contract as `seed_sample_events`), so the
  Catalyst Watch read model (Slice 61) and the event-risk guard (Slice 89)
  reflect provider events automatically.

## Notes

- Follows the `BaseNewsAdapter` pattern: the adapter is **not** re-exported from
  `data_sources/__init__.py` (avoids importing the service layer at package
  load); it is imported directly where used.
- `event_service` references the adapter type only under `TYPE_CHECKING`, so
  there is no runtime import cycle (adapter → service at runtime only).
- The System Ops `refresh_events` protocol (UI/ops integration, mirroring Slice
  23) is the next slice; this slice is backend infrastructure only, so no
  System Ops fixture / visual baseline change.
- Mock events stay descriptive and uncertain-status only — no buy/sell wording,
  no CONFIRMED future dates.

## Tests added

- `tests/test_event_calendar_adapter.py` — mock determinism, Protocol
  conformance, uncertain-future-only statuses, `refresh_events` ingest +
  idempotency, link attachment (`list_for_event_key("FOMC")`).

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_event_calendar_adapter.py
  tests/test_event_radar.py tests/test_api_event_radar.py
  tests/test_risk_guard_service.py -q` ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `docker compose run --rm api python -m pytest tests/test_event_calendar_adapter.py
  tests/test_event_radar.py tests/test_api_event_radar.py -q` ✅ passed
- `docker compose run --rm --no-deps api python -m ruff check
  finskillos/data_sources/event_adapter.py finskillos/services/event_service.py
  tests/test_event_calendar_adapter.py` ✅ All checks passed

## Known issues

- None. Real external calendar provider + System Ops `refresh_events` protocol
  are follow-up slices.
