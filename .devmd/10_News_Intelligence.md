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
Status: TODO
Implemented source adapters:
Impact mapping:
Notes:
Known issues:
```
