# 61 — Catalyst Watch DB Read Model Promotion

Date: 2026-05-28

## Goal

Promote `/api/event-radar` from a fixture-first shell to a live DB-backed
Catalyst Watch read model when a DB session is reachable.

## Implemented

- Wired `build_event_radar_view_model` into the FastAPI GET route.
- Preserved `X-FSO-Use-Fixture: 1` as an explicit deterministic fixture mode.
- Returned `source=live` with `dataState.calendarStatus=db_backed` when stored
  upcoming events exist.
- Returned `source=live` with `dataState.calendarStatus=empty` when the DB is
  reachable but no upcoming event rows exist.
- Mapped stored Event Radar view-model rows into the existing Catalyst Watch API
  contract, including high-risk rows, holdings-linked rows, linked news, date
  confidence, drivers, conflicts, interpretation, and watchpoints.
- Added API regressions for live DB-backed and live empty event calendars.

## Verification

- `docker compose -f docker-compose.yml build api`
- `docker compose -f docker-compose.yml run --rm --no-deps api pytest tests/test_api_event_radar.py -q`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts -g "Catalyst Watch renders"`
