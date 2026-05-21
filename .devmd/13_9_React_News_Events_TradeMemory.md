# 13.9 — React Tabs: News Intelligence · Catalyst Watch · Trade Memory

## Goal

Promote the three "narrative-heavy" tabs from the Slice-13.6
placeholder shell to fully implemented React pages, wrapping the
existing Slice 10 / 11 / 12 Python services.

Targeted modules:

```text
- News Intelligence  (finskillos.services.news_service)
- Catalyst Watch     (finskillos.services.event_service + event_risk_service)
- Trade Memory       (finskillos.services.trade_journal_service + reflection_service)
```

## UX Direction — v4.2 Evidence-to-Judgment

Slice 13.9 must use the v4.2 Evidence-to-Judgment prototype as the
primary UX direction:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

For each tab, avoid a simple table/card dump. The page should read
as:

```text
Judgment Header
→ Primary Drivers
→ Conflicts / Uncertainty
→ Evidence Details
→ Integrated Interpretation
→ Watchpoints / Review Conditions
```

This does not mean implementing pixel-perfect v4.2 styling in this
slice. It means the information hierarchy must let the user
understand how raw news/events/journal data combines into a
judgment-support view.

Allowed judgment types:

```text
- narrative state
- event exposure state
- process/reflection state
- data freshness state
- portfolio relevance state
```

Forbidden:

```text
- direct buy/sell recommendation
- order/execution controls
- guaranteed return language
```

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md
.devmd/13_7_React_Market_Analysis_Symbol.md     (camelCase API + shell pattern precedent)
.devmd/13_8_React_Risk_Mission_Ops.md           (POST protocol pattern precedent)

v4.1 visual shell baseline:
prototypes/ui/enhanced_dashboard_mockup/index.html

v4.2 Evidence-to-Judgment UX baseline:
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html

finskillos/services/news_service.py
finskillos/services/event_service.py
finskillos/services/event_risk_service.py
finskillos/services/trade_journal_service.py
finskillos/services/reflection_service.py
finskillos/ui/view_models/news_intelligence_vm.py
finskillos/ui/view_models/event_radar_vm.py
finskillos/ui/view_models/trade_memory_vm.py

frontend/src/pages/news-intelligence/NewsIntelligencePage.tsx
frontend/src/pages/catalyst-watch/CatalystWatchPage.tsx
frontend/src/pages/trade-memory/TradeMemoryPage.tsx
```

## Scope

Allowed:

```text
- Add FastAPI routes:
    GET  /api/news-intelligence
    POST /api/news-intelligence/manual-article
    GET  /api/event-radar
    POST /api/event-radar/manual-event
    POST /api/event-radar/seed-sample-events
    GET  /api/trade-memory
    POST /api/trade-memory/entries
    GET  /api/trade-memory/weekly-review
- Pydantic camelCase schemas (one file per domain).
- React pages replacing the placeholder shells.
- Tests at frontend/e2e/news-events-memory.spec.ts.
- Re-use the existing write-seam safety scans
  (TradeJournalService _assert_entry_text_is_safe,
  NewsService title/summary truncation, EventService CONFIRMED
  source guard).
```

Not allowed:

```text
- Add live news / event API adapters (paid feeds, RSS, etc.).
- Add LLM coaching or summarisation.
- Store full copyrighted article bodies.
- Auto-confirm uncertain events (must respect TENTATIVE / WINDOW /
  SPECULATIVE / REPORTED date_status).
- Surface raw service exceptions to the user.
- Add execution / brokerage controls anywhere.
```

## Required UI per tab

### News Intelligence — v4.2 target

News Intelligence should answer:

```text
What narrative is affecting my portfolio, and what evidence supports
that interpretation?
```

Required structure:

```text
Judgment Header:
- Narrative Judgment
- confidence
- dominant theme
- portfolio relevance
- event linkage
- sentiment / risk tone

Primary Drivers:
- affected holdings
- theme exposure
- linked event count
- source quality / freshness

Conflicts / Uncertainty:
- positive narrative vs event volatility
- article count vs source/date confidence
- broad market news vs holding-specific relevance

Evidence Details:
- holdings-relevant news
- impact map
- event-linked news
- manual article entry

Integrated Interpretation:
- what today's news means for portfolio context
- why it matters
- what remains uncertain

Watchpoints:
- source confirmation
- change in linked event status
- sudden cluster in same theme/ticker
```

Required components:

```text
features/news/components/NewsJudgmentHeader.tsx
features/news/components/HoldingsRelevantNews.tsx
features/news/components/NewsImpactMap.tsx
features/news/components/EventLinkedNewsPanel.tsx
features/news/components/ManualArticleEntry.tsx
features/news/components/NewsWatchpointsPanel.tsx
```

Manual article entry safety rules:

```text
- Summary input is hard-capped at MAX_SUMMARY_CHARS = 500.
- No "full article body" field.
- Disclaimer: "Short summaries only — no full article body stored."
- Stored fields only: title / source / url / published_at /
  short_summary / affected_tickers / theme / event_key /
  sentiment / risk tags.
```

API targets:

```text
GET  /api/news-intelligence
POST /api/news-intelligence/manual-article
```

### Catalyst Watch / Event Radar — v4.2 target

Catalyst Watch should answer:

```text
Which upcoming events create exposure, and why is the event risk
score high or low?
```

Required structure:

```text
Judgment Header:
- Event Exposure Judgment
- confidence
- highest-risk event
- cluster status
- portfolio-linked exposure
- date-confidence mix

Primary Drivers:
- portfolio exposure
- days to event
- date status
- regime multiplier
- linked news count

Conflicts / Uncertainty:
- confirmed event vs speculative event
- high news attention vs low date confidence
- event risk score is not price prediction

Evidence Details:
- upcoming event table
- date status badges
- high-risk events
- holdings-linked events
- linked news
- manual event entry
- sample event seed action

Integrated Interpretation:
- why the event deserves attention
- how it relates to portfolio exposure
- what makes the score uncertain

Watchpoints:
- speculative → reported/confirmed date status transition
- linked news count increase
- regime shift increasing/decreasing event multiplier
```

Required event status badges (colour coding preserved):

```text
CONFIRMED   → success
WINDOW      → info
TENTATIVE   → warning
REPORTED    → warning
SPECULATIVE → purple
```

Required components:

```text
features/events/components/EventExposureJudgment.tsx
features/events/components/EventRiskTable.tsx
features/events/components/EventStatusBadge.tsx
features/events/components/HighRiskEventsPanel.tsx
features/events/components/HoldingsLinkedEventsPanel.tsx
features/events/components/EventScoreDrivers.tsx
features/events/components/ManualEventEntry.tsx
features/events/components/EventLinkedNewsPanel.tsx
```

Manual event entry safety rules:

```text
- date_status defaults to TENTATIVE.
- CONFIRMED + source="manual_seed" rejected by the existing
  EventService validator.
- "Seed sample events" stays idempotent (existing
  seed_sample_events helper).
```

API targets:

```text
GET  /api/event-radar
POST /api/event-radar/manual-event
POST /api/event-radar/seed-sample-events
```

Important wording rule:

```text
Event risk score = preparation / exposure score only.
It must never be described as price direction prediction.
```

### Trade Memory — v4.2 target

Trade Memory should answer:

```text
What repeated behavior pattern is visible, and what should I review
before the next week?
```

Required structure:

```text
Judgment Header:
- Process Judgment
- confidence
- best condition
- weakest condition
- repeated mistake
- review priority

Primary Drivers:
- recent entries
- PnL by regime
- PnL by sector/theme
- PnL by strategy
- mistake frequency
- emotion tags before losses

Conflicts / Uncertainty:
- good market regime vs poor process behavior
- high win rate vs clustered mistakes
- short sample size limitations

Evidence Details:
- recent entries table
- add journal entry form
- weekly review panel
- performance by regime
- performance by sector/theme
- performance by strategy
- mistake frequency
- copyable weekly review markdown

Integrated Interpretation:
- what pattern appeared this week
- what condition helped
- what condition harmed
- what review condition matters next

Watchpoints:
- chasing before event windows
- oversizing in overheat regime
- emotion tag clustering before losses
```

Required components:

```text
features/trades/components/ProcessJudgmentHeader.tsx
features/trades/components/RecentEntriesTable.tsx
features/trades/components/TradeEntryForm.tsx
features/trades/components/WeeklyReviewPanel.tsx
features/trades/components/PerformanceByRegime.tsx
features/trades/components/PerformanceBySectorTheme.tsx
features/trades/components/PerformanceByStrategy.tsx
features/trades/components/MistakeFrequencyPanel.tsx
features/trades/components/WeeklyMarkdownExport.tsx
features/trades/components/TradeMemoryWatchpoints.tsx
```

Form / safety rules:

```text
- side selector limited to LONG / SHORT / WATCH / EXIT_REVIEW /
  OTHER (legacy BUY/SELL load-only).
- Caption: "Reflection / process review — no execution controls."
- Copyable weekly-review markdown text_area already produced by
  TradeMemoryViewModel.weekly_review_markdown.
```

API targets:

```text
GET  /api/trade-memory
POST /api/trade-memory/entries
GET  /api/trade-memory/weekly-review
```

## Safety contract (must re-enforce)

```text
- Manual article summary input: maxLength 500, no full body field.
- Manual event input: rejects CONFIRMED + manual_seed source.
- Manual trade journal input passes through
  TradeJournalService._assert_entry_text_is_safe on the server
  before persistence.
- No execution captions anywhere (Buy / Sell / Execute / Trade Now /
  Order / Place Order / 지금 사라 / 지금 팔아라 / 매수 버튼 /
  매도 버튼).
- "sell-the-news" remains allowed as a descriptive market idiom.
```

## Required tests

```text
frontend/e2e/news-events-memory.spec.ts
```

Assertions:

```text
- /news-intel renders manual article entry + impact map.
- /catalyst-watch renders date-status badges and manual event entry.
- /trade-memory renders the weekly-review markdown text area and the
  mistake frequency table.
- POST /api/news-intelligence/manual-article rejects a body longer
  than MAX_SUMMARY_CHARS.
- POST /api/event-radar/manual-event rejects CONFIRMED + manual_seed.
- POST /api/trade-memory/entries rejects forbidden wording.
- No forbidden execution captions appear anywhere.
- "sell-the-news" descriptive idiom does NOT trip the wording guard.
```

Backend:

```text
tests/test_api_news_intelligence.py
tests/test_api_event_radar.py
tests/test_api_trade_memory.py
```

## Verification commands

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q
python3 -m ruff check finskillos api tests

cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e

docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e
```

## Completion placeholder

```text
Status: TODO
Implemented routes:
Implemented React pages:
Safety contract enforced:
Tests added:
Notes:
Known issues:
```

## Stop condition

Stop after 13.9. Do not start 13.10 unless the user explicitly asks.
