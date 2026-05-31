# 97 — Market Kernel Live Event Overlay

Date: 2026-05-30

## Goal

First half of the "Market Kernel event overlay + multi-timeframe" item. The
Market Kernel response already carried an `events: list[EventOverlayItem]` field
and the React `EventOverlayPanel`, but the live route hard-coded `events = []`
and `event_overlay_status = "MISSING"`. Populate the overlay with live Catalyst
Watch events relevant to the selected ticker.

## Implemented

- `api/routes/market_kernel.py`:
  - `_live_response` now receives the `session` and computes a ticker-relevant
    event overlay (`_event_overlay`): upcoming events (via the de-duplicated
    `EventService.list_upcoming`, Slice 96) where the ticker is among the event's
    linked tickers, **or** the event is market-wide macro (no ticker link, e.g.
    FOMC / CPI). Each item maps to `EventOverlayItem` (days-to-event, title,
    `event_type · relevance` subtitle, `date_status` tag, tone from the Slice-11
    `EventRiskService` risk label). Capped at 6.
  - `event_overlay_status` is now `AVAILABLE` when the overlay has items, else
    `MISSING`, in both the with-bars and no-bars branches.
  - `_overlay_tone` maps CRITICAL/HIGH/MODERATE/LOW → danger/warning/info/neutral.

## Tests added

- `tests/test_api_market_kernel.py::test_market_kernel_event_overlay_includes_relevant_events`
  — live DB with NVDA bars + a NVDA-linked earnings event + a macro FOMC event +
  an unrelated TSLA event: the overlay includes the NVDA and FOMC events,
  excludes TSLA, sets `eventOverlayStatus="AVAILABLE"`, and each item has the
  expected camelCase shape.

## Notes

- Live-path only: the `use_fixture` / forced-fixture path (and the Market Kernel
  visual baseline) is unchanged — the fixture already ships sample overlay
  events. No baseline regeneration.
- Reuses Slice-96 dedup, so duplicate-title events never double up in the
  overlay either. Descriptive only — no execution wording.
- Multi-timeframe query is the next slice.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_market_kernel.py -q`
  ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check api/routes/market_kernel.py tests/test_api_market_kernel.py`
  ✅ All checks passed
- `docker compose run --rm api python -m pytest tests/test_api_market_kernel.py
  tests/test_event_dedup.py -q` ✅ passed

## Known issues

- Multi-timeframe (`?timeframe=` like Symbol Lab) remains the follow-up half.
