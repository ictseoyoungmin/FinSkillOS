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
Status: TODO
Implemented views:
Seed events:
Notes:
Known issues:
```
