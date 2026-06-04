# 165 — Event/News/Position Linkage Scoring (Phase 4)

**Status:** Done. Read-only. Makes each event's risk score explainable and shows
the event↔position linkage.

`EventRiskService` already multiplies importance × exposure-weight × proximity-
weight × overheat-weight into `event_risk_score`, but the API dropped the factor
breakdown and never said which *held* positions an event actually touches. This
slice surfaces both.

## Implemented

### API / VM
- `EventRiskVM` gains `score_drivers: tuple[(label, value), …]` (the multiplicative
  factors: Importance, Portfolio exposure %, Exposure/Proximity/Overheat weights,
  Linked news count, final Event risk score) + `held_tickers` (the affected
  tickers that are actually in the account's positions). `_build_event_risk_vm`
  now receives `holdings_tickers` and intersects.
- `EventRiskRow` schema gains `score_drivers: list[EventScoreDriver]` +
  `held_tickers: list[str]`; the route maps them. Empty in fixtures.

### Frontend
- `EventRiskTable` gains a per-event "Score & linkage" `<details>` row (factor
  grid + "Held positions touched: …"); affected-ticker tags that are held are
  highlighted. Rendered only when score drivers exist → fixture render unchanged,
  Event Radar visual baseline intact.

## Tests (`tests/test_api_event_radar.py`, extended live test)
- with a held NVDA position and an NVDA-linked earnings event: the row's
  `scoreDrivers` include `Importance` + `Event risk score`, and `heldTickers ==
  ["NVDA"]`.

## Verification
- Offline: event-radar + news + safety-language + v42 pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt images): `docker compose build api web` → api pytest + ruff +
  web build.

## Notes
- No migration. Score breakdown reuses the existing `EventRiskBreakdown`; linkage
  is an in-memory intersection with current holdings. Live-gated by data → no
  Playwright regen.
- Next: 166 Portfolio Constraint Summary v2.
