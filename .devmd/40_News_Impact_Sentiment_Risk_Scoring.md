# 40 — News Impact Sentiment / Risk Scoring

## Goal

Reduce low-value `UNKNOWN` labels in News Intelligence and Symbol Lab by
deriving deterministic, metadata-only sentiment and risk labels from stored
RSS/manual article titles and short summaries.

The system should:

- store sentiment/risk labels when new articles are ingested;
- keep classification descriptive only, with no price prediction or action
  language;
- improve existing stored article display without requiring DB rewrites;
- keep News Intelligence and Symbol Lab reading the same rule set.

## Design

`NewsService` owns the shared scoring helper:

- sentiment: `POSITIVE`, `NEGATIVE`, `MIXED`, or `UNKNOWN`;
- risk: `GREEN`, `YELLOW`, `ORANGE`, `RED`, or `UNKNOWN`;
- inputs: article title plus the capped short summary only.

Rules are keyword based and conservative:

- strong/beat/upgrade/contract/approval style cues map positive and generally
  green;
- weak/miss/downgrade/delay/volatility cues map negative or mixed and yellow;
- probe/lawsuit/investigation/regulatory cues map orange;
- fraud/default/breach/halt/crash style cues map red.

Manual or classifier impacts keep caller-provided labels when they are not
`UNKNOWN`; otherwise they are enriched from the article text.

## Implemented

- Expanded `NewsService` keyword scoring vocabulary.
- Added `infer_news_signal(title + summary)` as the shared scoring seam.
- New article ingestion now persists enriched sentiment/risk labels on
  `news_impacts`.
- `GET /api/news-intelligence` applies the same scoring as a read-time fallback
  for older stored impact rows that still contain `UNKNOWN`.
- Symbol Lab ticker-linked news applies the same read-time sentiment fallback.
- Regression tests cover positive, negative, material-risk, and manual-impact
  enrichment paths.

## Out of Scope

- LLM or paid vendor sentiment analysis.
- Full article crawling or long body storage.
- Historical DB rewrite/migration for old `UNKNOWN` rows. Existing rows render
  with read-time fallback, and future refresh/re-ingest persists labels.

## Validation

```bash
python3 -m ruff check finskillos/services/news_service.py api/routes/news_intelligence.py finskillos/ui/view_models/symbol_lab_vm.py tests/test_news_intelligence.py
timeout 90 env FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_news_intelligence.py tests/test_api_news_intelligence.py tests/test_api_symbol_lab.py -q
docker compose -f docker-compose.yml exec -T web npm run build
docker compose -f docker-compose.yml exec -T web npm run lint
```
