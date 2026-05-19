# 10 — Research Hub: News & Intelligence

## Goal

Implement news ingestion, classification, portfolio impact mapping, and interpretation.

## Purpose

News should not be a raw feed. It should answer:

```text
Which news matters to my holdings?
Which sector/theme does it affect?
Is it event-linked?
Is it likely to increase risk, sentiment, or volatility?
```

## News categories

```text
Market News
Macro News
Sector News
Symbol News
Event-linked News
Position-relevant News
```

## Data model

Use:

```text
news_articles
news_impacts
```

`news_articles` stores title/source/url/published time/summary.  
`news_impacts` links the article to tickers, sectors, events, impact score, sentiment, and risk notes.

## MVP data source

Start with manual input or simple RSS/API adapter. Do not block the MVP on paid data sources.

## Required UI

```text
Filter by holdings only
Filter by watchlist
Filter by sector/theme
Filter by date range
Impact score
Sentiment label
AI/template summary
Affected holdings
Risk note
```

## Interpretation example

```text
TSLA-related headlines are improving short-term sentiment.
However, event expectation is rising before the SpaceX/Tesla catalyst window.
Watch for weak price reaction despite positive news.
```

## Safety

Do not generate article-length copyrighted reproductions. Store and display short summaries and links.

## Files

```text
finskillos/services/news_service.py
finskillos/services/news_impact_service.py
finskillos/ui/pages/news_intelligence.py
finskillos/db/models/news.py
```

## Acceptance criteria

- News article can be inserted manually or via adapter.
- News can be linked to tickers/sectors/events.
- News impact is visible in News & Intelligence.
- Event Radar can show event-linked news.
- No long copyrighted text is stored/displayed.
- News summary avoids deterministic market predictions.

## Test commands

```bash
pytest tests/test_news_intelligence.py -q
```

## Completion placeholder

```text
Status: DONE_AS_NEWS_INTELLIGENCE_V0 (2026-05-19)

Implemented:
- news_articles / news_impacts ORM models
  (finskillos/db/models/news.py) with short-form storage limits
  (MAX_TITLE_CHARS=300, MAX_SUMMARY_CHARS=500). No full_text /
  article_body / body / content columns exist by design.
- Alembic migration 0005_news_intelligence creates both tables plus
  the documented indexes (idx_news_articles_published /
  _source, idx_news_impacts_ticker / sector / theme / event_key /
  event_linked, idx_news_ticker_date).
- NewsArticleRepository + NewsImpactRepository
  (finskillos/db/repositories/news_repo.py). Article upsert is keyed
  on url; impact upsert is keyed on the
  (article, ticker, sector, theme, event_key) composite tuple so
  re-classification does not multiply rows.
- NewsService (finskillos/services/news_service.py): ingest_article
  truncates oversized title/summary, applies the deterministic
  keyword classifier (TSLA / NVDA / AAPL / MSFT / AMZN ticker rules
  + AI / chip / SpaceX / data-center theme rules + Fed / CPI /
  earnings / delivery event rules) plus substring-based sentiment
  detection (POSITIVE / NEUTRAL / NEGATIVE / MIXED / UNKNOWN).
- BaseNewsAdapter Protocol
  (finskillos/data_sources/news_adapter.py) + MockNewsAdapter
  (finskillos/data_sources/adapters/sample_news_adapter.py) for
  deterministic seed / test paths. No live HTTP / paid APIs.
- NewsIntelligenceViewModel
  (finskillos/ui/view_models/news_intelligence_vm.py) — latest,
  holdings-relevant, event-linked tuples plus aggregated
  affected_tickers / affected_sectors. UI-seam safety scan re-checks
  title/summary length and reuses assert_no_forbidden_wording.
- News Intelligence Streamlit page
  (finskillos/ui/pages/news_intelligence.py) — summary chips,
  holdings-relevant / latest / event-linked tables, impact map,
  manual entry expander (Title / Source / URL / published date /
  Short summary with max_chars=500 + optional ticker / sector /
  theme). Direct buy/sell button captions are forbidden.
- App shell NEWS_INTELLIGENCE nav item + dispatch (placed after
  SYMBOL_LAB).
- Symbol Lab integration: SymbolNewsVM + SymbolLabViewModel.news
  field. _build_news_for_ticker calls
  NewsService.list_articles_for_ticker (with defensive try/except so
  Symbol Lab still renders on Slice-09 DBs without the news tables
  applied). assert_symbol_lab_view_model_is_safe scans
  news.title / sentiment_label / risk_note as well.

Implemented source adapters:
- Manual input (Streamlit form + NewsService.ingest_article)
- MockNewsAdapter (in-memory deterministic adapter behind
  BaseNewsAdapter Protocol)
- No live API adapter — intentionally deferred.

Impact mapping:
- ticker  (TSLA / NVDA / AAPL / MSFT / AMZN)
- sector  (Consumer Discretionary / Semiconductors / Technology /
  Infrastructure / Macro)
- theme   (EV / AI / Space / Data Center / Macro)
- event_key (SPACE_LAUNCH / FED_DECISION / MACRO_PRINT / EARNINGS /
  DELIVERY)
- impact_score (Decimal 0.3–0.5 per rule)
- sentiment_label (POSITIVE / NEUTRAL / NEGATIVE / MIXED / UNKNOWN)
- risk_level (GREEN / YELLOW / ORANGE / RED / UNKNOWN, default
  UNKNOWN; macro / Fed rules emit YELLOW)
- risk_note  (manual / extra_impacts only — classifier leaves it
  null in v0)
- volatility_note (manual / extra_impacts only — null in v0)
- is_event_linked (True for SpaceX / Fed / CPI / earnings / delivery
  rule matches)

Scope note:
- Slice 10 is complete as News Intelligence v0. Live news APIs
  (paid or RSS), LLM summarisation, fine-grained source-reliability
  scoring, multi-language sentiment, and full Event Radar
  integration are intentionally deferred to later slices.

Tests added:
- tests/test_news_intelligence.py (24 cases)
- tests/test_news_intelligence_ui.py (9 cases)

Verification (all green on 2026-05-19):
- python3 -m compileall app.py finskillos scripts
- python3 -m pytest tests/test_news_intelligence.py
                    tests/test_news_intelligence_ui.py -q
- python3 -m pytest tests/test_symbol_lab_view_model.py
                    tests/test_symbol_lab_ui.py
                    tests/test_index_lab_view_model.py
                    tests/test_analysis_workspace_ui.py
                    tests/test_ui_view_models.py
                    tests/test_control_room_ui.py -q
- python3 -m pytest tests -q   (full suite, 316 cases)
- python3 -m ruff check finskillos/db finskillos/services
                        finskillos/ui
                        tests/test_news_intelligence.py
                        tests/test_news_intelligence_ui.py
- python3 -m pytest tests/integration/test_db_migrations.py -q
  (alembic upgrade head smoke against in-memory SQLite)

Notes:
- The .devmd/10 spec and the older docs/v2_1/03 §news_articles
  design differ (the doc uses a TEXT[] tickers column + a JSON
  affected_positions blob; the slice spec uses a granular
  news_impacts row per ticker/sector/theme/event). We follow the
  slice spec because it lets Symbol Lab + Event Radar do a direct
  index lookup without unpacking JSON.
- NewsService.ingest_article never stores long copyrighted text:
  title / summary are truncated and an ellipsis marker is appended
  so the UI can signal truncation.
- The keyword classifier is intentionally rule-first, not LLM-based.
  Adding LLM enrichment in a later slice should slot into
  classify_impacts without touching the persistence layer.

Known issues:
- Paid / live news APIs (Bloomberg / Reuters / GDELT / etc.) remain
  out of scope. Only MockNewsAdapter + manual entry are wired.
- LLM-based article summarisation / sentiment remains out of scope.
- Long copyrighted article storage / display remains intentionally
  unsupported (the schema has no field for it).
- News impact scoring remains deterministic rule-first v0; the
  numeric impact_score is a coarse 0.3 / 0.4 / 0.5 ladder.
- Full Event Radar integration remains deferred to Slice 11.
- Trade Memory remains deferred to Slice 12.
- Brokerage / trade execution remains out of scope.
```

```text
Post-Slice-10 Cleanup Status: DONE (2026-05-19)

Changed files:
- finskillos/db/repositories/news_repo.py
- finskillos/services/news_service.py
- tests/test_news_intelligence.py
- .devmd/10_News_Intelligence.md

Behavior change:
- NewsService.ingest_article gained replace_impacts=True (default).
  On re-ingest of an existing URL the desired impact set (classifier
  + extra_impacts, deduplicated by the
  (ticker, sector, theme, event_key) key) is computed first; any
  existing impact whose key is no longer in that set is deleted
  before the upsert pass. replace_impacts=False keeps the previous
  append/update behaviour for the few callers that want it.
- NewsImpactRepository.delete(impact) was added so the service can
  drop a stale row without touching the SQLAlchemy session directly.
- _normalize_impact_input + _impact_key + _dedupe_impact_inputs were
  added to news_service: ticker is uppercased, empty-string sector /
  theme / event_key collapse to None, and the dedupe pass keeps the
  first occurrence of each impact key so callers cannot create two
  rows that the repository key would treat as identical.
- ingest_article now feeds classifier output first, then
  extra_impacts (preserving caller overrides on a classified key),
  before normalization and dedupe.
- Tests pin the new contract:
    - test_reingest_replaces_stale_classifier_impacts
    - test_reingest_with_no_impact_clears_existing_impacts
    - test_reingest_can_preserve_old_impacts_when_replace_disabled
    - test_manual_impact_ticker_is_normalized_to_uppercase
    - test_manual_impact_key_dedupes_lowercase_and_uppercase_ticker
  The previously-passing duplicate-URL / multi-impact / Symbol Lab
  ticker-news tests remain green.

Verification:
- python3 -m compileall app.py finskillos scripts                                          ✅ no errors
- python3 -m pytest tests/test_news_intelligence.py
                    tests/test_news_intelligence_ui.py -q                                  ✅ 39 passed
- python3 -m pytest tests/test_symbol_lab_view_model.py
                    tests/test_symbol_lab_ui.py -q                                         ✅ 31 passed
- python3 -m pytest tests -q                                                               ✅ 321 passed
- python3 -m ruff check finskillos/db finskillos/services
                        tests/test_news_intelligence.py                                    ✅ All checks passed

Known issues:
- Live / paid news adapters remain out of scope.
- LLM-based article summarization remains out of scope.
- Full Event Radar integration remains deferred to Slice 11.
- Source reliability scoring remains deferred.
```
