# 11 — Event Radar

## Goal

Implement event calendar and event-to-portfolio risk mapping.

## Purpose

Event Radar helps the user prepare for catalysts instead of reacting emotionally.

## Event types

```text
IPO window
Earnings
Macro
Central bank
Inflation
Product event
Launch event
Regulatory
Sector conference
```

## Initial events

Seed examples:

```text
SpaceX IPO expected window
Tesla shareholder / robotaxi event
NVIDIA earnings
FOMC
CPI / PPI
Rocket launch schedule
AI regulation updates
```

Dates should be editable. Do not hardcode uncertain future events as facts.

## Event risk score

Suggested formula:

```text
event_risk_score =
importance
× portfolio_exposure
× days_to_event_weight
× market_overheat_weight
```

## Required UI

```text
Upcoming events table
Calendar view
Affected sectors
Affected holdings
Pre-event risk notes
Post-event reversal risk notes
Event-linked news
```

## Files

```text
finskillos/services/event_service.py
finskillos/services/event_risk_service.py
finskillos/ui/pages/event_radar.py
```

## Acceptance criteria

- User can create/edit event.
- Event can link to themes and tickers.
- Event risk score changes based on portfolio exposure.
- Event-linked news appears when available.
- UI differentiates known date vs date window vs speculative event.
- Uncertain events are labeled as tentative or reported.

## Test commands

```bash
pytest tests/test_event_radar.py -q
```

## Completion placeholder

```text
Status: DONE_AS_EVENT_RADAR_V0 (2026-05-19)

Implemented:
- events / event_links ORM models (finskillos/db/models/event.py)
  with explicit event_type / date_status vocabularies (CONFIRMED /
  WINDOW / TENTATIVE / REPORTED / SPECULATIVE / UNKNOWN).
- Alembic migration 0006_event_radar creates both tables + documented
  indexes (idx_events_date / _end_date / _type / _date_status,
  idx_event_links_ticker / sector / theme / event_key).
- EventRepository + EventLinkRepository
  (finskillos/db/repositories/event_repo.py).
- EventService (finskillos/services/event_service.py): create /
  update / link, list_upcoming, list_for_event_key,
  list_holdings_relevant, seed_sample_events (idempotent by title).
- Service-level guard rejects CONFIRMED events that cite a seed
  source — uncertain future dates MUST use WINDOW / TENTATIVE /
  SPECULATIVE.
- EventRiskService (finskillos/services/event_risk_service.py):
  deterministic event_risk_score formula (importance ×
  portfolio_exposure_weight × days_to_event_weight ×
  market_overheat_weight), clamped to 0–10, mapped to LOW / MODERATE
  / HIGH / CRITICAL labels. Portfolio exposure derives from latest
  PortfolioSnapshot when available, otherwise from the live positions
  total. Theme-only / sector-only events (FOMC / CPI / regulatory)
  still score because they describe market-level exposure even when
  no individual position is held.
- Event-linked news join via news_impacts.event_key / .ticker
  (Slice-10 integration). Only is_event_linked impacts participate.
- EventRadarViewModel + assert_event_radar_view_model_is_safe
  (finskillos/ui/view_models/event_radar_vm.py) — upcoming /
  high_risk / holdings_linked tuples + deterministic
  pre_event_note / post_event_note (the post-event note
  intentionally surfaces the descriptive "sell-the-news" idiom).
- Catalyst Watch / Event Radar Streamlit page
  (finskillos/ui/pages/event_radar.py): summary chips, three event
  tables, per-event expander with linked news, sample-seed button,
  manual entry form. Manual form only exposes uncertain status
  choices by default and rejects CONFIRMED-without-source server
  side.
- App shell CATALYST_WATCH dispatch now routes to
  finskillos.ui.pages.event_radar. The deferred placeholder
  ``render_catalyst_watch`` was removed; only Trade Memory remains
  in deferred.py.

Implemented views:
- Upcoming events table (date status badge, days-to-event, importance,
  risk score, risk label, tickers / sectors / themes).
- High-risk events (event_risk_score ≥ 4.0).
- Holdings-linked events (linked ticker matches default-account
  positions).
- Event-linked news (per-event expander, joined via news_impacts).
- Manual event entry form + sample seed button.

Seed events (all uncertain, never CONFIRMED):
- SpaceX IPO expected window → SPECULATIVE window (60–90 days out).
- Tesla shareholder / robotaxi event → TENTATIVE.
- NVIDIA earnings → TENTATIVE.
- FOMC rate decision → WINDOW (14–15 days out).
- CPI release → TENTATIVE.
- PPI release → TENTATIVE.
- Rocket launch schedule → TENTATIVE.
- AI regulation update → TENTATIVE.

Tests added:
- tests/test_event_radar.py (24 cases)
- tests/test_event_radar_ui.py (8 cases)

Verification (all green on 2026-05-19):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_event_radar.py
                    tests/test_event_radar_ui.py -q
- python3 -m pytest tests/test_news_intelligence.py
                    tests/test_news_intelligence_ui.py
                    tests/test_symbol_lab_view_model.py
                    tests/test_symbol_lab_ui.py -q
- python3 -m pytest tests -q   (full suite, 356 cases)
- python3 -m ruff check finskillos/db finskillos/services
                        finskillos/ui
                        tests/test_event_radar.py
                        tests/test_event_radar_ui.py
- python3 -m pytest tests/integration/test_db_migrations.py -q
  (alembic upgrade head smoke against in-memory SQLite)

Notes:
- The .devmd/11 spec uses granular event_links rows; docs/v2_1/03
  §events sketches a TEXT[] tickers + JSONB affected_themes column
  layout instead. We follow the slice spec because it lets Symbol
  Lab + portfolio-exposure lookups stay a direct index hit and
  mirrors the news_impacts pattern from Slice 10.
- Event dates are editable. EventService rejects CONFIRMED rows
  that cite a seed source so uncertain future dates cannot be
  silently relabeled as facts.
- event_risk_score is an exposure / preparation score, NOT a
  prediction. Risk label thresholds: LOW <2 / MODERATE <4 /
  HIGH <7 / CRITICAL.
- assert_event_radar_view_model_is_safe reuses the hardened guard
  forbidden-wording regex so direct-advice wording (BUY / SELL /
  매수 / 매도) cannot leak through event title / pre or post-event
  note / linked news title or summary / sector or theme label /
  setup hint. The market idiom "sell-the-news" remains explicitly
  allowed (the default post-event note depends on it).

Known issues:
- Full calendar-grid UI remains deferred (Slice 11 v0 ships a
  table layout only).
- Live external event feeds (Bloomberg, FactSet, exchange
  calendars, BLS/Fed scrapers, …) remain out of scope.
- Exact future event dates must not be inferred without
  user / source input; the seeder only ships uncertain placeholders.
- Trade Memory remains deferred to Slice 12.
- Brokerage / trade execution remains out of scope.
```

```text
Post-Slice-11 Cleanup Status: DONE (2026-05-19)

Changed files:
- finskillos/db/repositories/event_repo.py
- finskillos/services/event_service.py
- finskillos/ui/pages/event_radar.py
- tests/test_event_radar.py
- tests/test_event_radar_ui.py
- .devmd/11_Event_Radar.md

Behavior change:
- EventRepository.update_event() now distinguishes "field omitted"
  from "explicitly cleared" via a private _UNSET sentinel on
  nullable fields (end_date / source / source_url / description).
  Passing None on those kwargs clears the row; omitting the kwarg
  leaves it unchanged. Non-null fields keep the legacy "None means
  skip" idiom.
- EventService.update_event() passes the full EventInput nullable
  values through intentionally, so editing a WINDOW event back to a
  single-date TENTATIVE entry no longer leaves a stale end_date.
- EventService.list_for_event_key() no longer queries EventLink
  through the raw session; it routes through new
  EventLinkRepository.list_for_event_key() so future Catalyst Watch
  / news join logic can reuse the same repo-level query.
- EventLinkRepository.add_or_update_link() now normalises ticker
  (uppercase + trim) and collapses empty/whitespace sector / theme
  / event_key dimension strings to None at the repository seam. A
  direct repo call with ticker="tsla" then ticker="TSLA" now produces
  a single canonical row.
- Event Radar page caption explicitly notes that event_risk_score is
  an exposure / preparation score, not a prediction
  (`이 점수는 가격 예측이 아니라 ...` + English mirror).
- Tests pin the new contract:
    - test_update_event_can_clear_nullable_fields
    - test_update_event_repo_partial_update_keeps_unset_fields
    - test_event_link_repository_lists_by_event_key
    - test_event_service_list_for_event_key_uses_repo
    - test_event_link_repository_normalizes_ticker_case
    - test_event_link_repository_collapses_empty_dimension_strings
    - test_event_radar_page_describes_score_as_not_prediction

Verification:
- python3 -m compileall app.py finskillos scripts                                          ✅ no errors
- python3 -m pytest tests/test_event_radar.py
                    tests/test_event_radar_ui.py -q                                        ✅ 39 passed
- python3 -m pytest tests/test_news_intelligence.py
                    tests/test_news_intelligence_ui.py -q                                  ✅ 40 passed
- python3 -m pytest tests -q                                                               ✅ 363 passed
- python3 -m ruff check finskillos/db finskillos/services finskillos/ui
                        tests/test_event_radar.py
                        tests/test_event_radar_ui.py                                       ✅ All checks passed

Known issues:
- Full calendar-grid UI remains deferred.
- Live external event feeds remain out of scope.
- Source reliability scoring remains deferred.
- Trade Memory remains deferred to Slice 12.
- Brokerage / execution remains out of scope.
```
