# 58 — Catalyst Watch Source Date Confidence

Date: 2026-05-28

## Goal

Make Catalyst Watch explicit about two separate facts:

- whether the event calendar itself is fixture-first or DB-backed,
- how much date confidence exists across upcoming events.

This avoids confusing a live DB session with a live Catalyst calendar read
model.

## Implemented

- Added `dataState` to the `/api/event-radar` response contract.
- Captured calendar source/status, event count, linked-news count, confirmed
  count, uncertain count, nearest-event timing, and date-confidence summary.
- Added a compact Catalyst Watch state band for:
  - calendar source,
  - date confidence,
  - event rows / linked news,
  - DB / read mode.
- Kept manual event entry behavior unchanged for this slice.
- Added API and Playwright assertions for the new state band/contract.

## Verification

- `docker compose -f docker-compose.yml build api web`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_event_radar.py -q`
- `docker compose -f docker-compose.yml run --rm --no-deps web npm run build`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Catalyst Watch renders"`
