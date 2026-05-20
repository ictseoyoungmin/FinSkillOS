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

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md
.devmd/13_7_React_Market_Analysis_Symbol.md     (camelCase API + shell pattern precedent)
.devmd/13_8_React_Risk_Mission_Ops.md           (POST protocol pattern precedent)
prototypes/ui/enhanced_dashboard_mockup/finskillos_v4_1_product_cockpit_index.html

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

### News Intelligence

```text
- Latest news cards/table (title / source / published_at /
  sentiment / impact tags).
- Holdings-relevant news section (matched via position tickers).
- Impact map (affected tickers + sectors + themes).
- Event-linked news badge (rows where is_event_linked = True).
- Manual article entry form (title / source / url / published_at /
  short summary + optional ticker / sector / theme / event_key).
  - Summary input is hard-capped at MAX_SUMMARY_CHARS = 500.
  - No "full article body" field.
- Disclaimer: "Short summaries only — no full article body stored."
```

Components:

```text
features/news/components/LatestNewsTable.tsx
features/news/components/HoldingsRelevantNews.tsx
features/news/components/NewsImpactMap.tsx
features/news/components/EventLinkedNewsPanel.tsx
features/news/components/ManualArticleEntry.tsx
```

### Catalyst Watch / Event Radar

```text
- Upcoming events table sorted by start_date.
- Date status badges with explicit colour coding:
    CONFIRMED → success
    WINDOW    → info
    TENTATIVE → warning
    REPORTED  → warning
    SPECULATIVE → purple
- Event risk score column with caption "Preparation / exposure
  score, not a prediction." — re-use the cleanup wording from
  .devmd/cleanup/11_cleanup.md Task 4.
- High-risk events callout (score ≥ 7).
- Holdings-linked events panel (events where any link.ticker is in
  current positions).
- Linked-news panel (joins news_impacts.event_key /
  news_impacts.ticker).
- Manual event entry form (title / event_type / date_status /
  start_date / optional end_date / importance / source / description
  + optional ticker / sector / theme / event_key).
  - date_status defaults to TENTATIVE.
  - CONFIRMED + source="manual_seed" must be rejected via existing
    EventService validator.
- "Seed sample events" button (idempotent, uses existing
  seed_sample_events helper).
```

Components:

```text
features/events/components/EventRiskTable.tsx
features/events/components/EventStatusBadge.tsx
features/events/components/HighRiskEventsPanel.tsx
features/events/components/HoldingsLinkedEventsPanel.tsx
features/events/components/EventLinkedNewsPanel.tsx
features/events/components/ManualEventEntry.tsx
features/events/components/SeedSampleEventsButton.tsx
```

### Trade Memory

```text
- Recent entries table (date / ticker / side / strategy / regime /
  sector / emotion / P&L / R / mistake tags).
- Add journal entry form (side selector limited to LONG / SHORT /
  WATCH / EXIT_REVIEW / OTHER — legacy BUY/SELL load-only).
- Weekly review panel: trade count / total P&L / win rate /
  best regime / weakest regime / process notes.
- Performance breakdowns (by regime, by sector/theme, by strategy).
- Mistake-tag frequency table.
- Copyable weekly-review markdown text_area (already produced by
  TradeMemoryViewModel.weekly_review_markdown).
- Caption: "Reflection / process review — no execution controls."
```

Components:

```text
features/trades/components/RecentEntriesTable.tsx
features/trades/components/TradeEntryForm.tsx
features/trades/components/WeeklyReviewPanel.tsx
features/trades/components/PerformanceByRegime.tsx
features/trades/components/PerformanceBySectorTheme.tsx
features/trades/components/PerformanceByStrategy.tsx
features/trades/components/MistakeFrequencyPanel.tsx
features/trades/components/WeeklyMarkdownExport.tsx
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
