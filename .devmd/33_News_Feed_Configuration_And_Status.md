# 33 — News Feed Configuration / Worker / Status Integration

## Goal

Make News Intelligence useful without requiring the user to manually maintain a
single RSS URL.

The system should:

- derive a news feed query from the current subscribed / focus tickers;
- allow explicit feed overrides through env;
- keep ingestion metadata-only and descriptive-only;
- expose news refresh availability and freshness through System Status;
- keep worker, System Ops, and News Intelligence reading the same policy.

## Design

Feed selection order:

1. `FINSKILLOS_NEWS_RSS_FEEDS` explicit comma/semicolon-separated feed URLs.
2. Generated Google News RSS search feed from configured/subscribed tickers.

Ticker seed order:

1. active `symbol_subscriptions` from DB;
2. `FINSKILLOS_NEWS_RSS_TICKERS`;
3. `FINSKILLOS_MARKET_REFRESH_TICKERS`;
4. built-in focus list for first-run usefulness.

The generated feed is still RSS metadata only. The adapter stores title, source,
URL, published timestamp, and short summary through `NewsService`.

## Scope

Implemented:

- shared news feed policy helper;
- worker and System Ops use the same feed policy;
- system-status exposes `refresh_news` availability;
- system-status latest summary includes `latestNewsAt`;
- tests cover generated feed URL and protocol availability.

Out of scope:

- paid/vendor news APIs;
- full article crawling;
- user-facing feed editor UI;
- per-folder feed policies.

## Validation

```bash
timeout 180 python3 -m pytest -q
python3 -m ruff check api/routes/health.py api/routes/system_ops.py finskillos/services/news_feed_policy.py scripts/refresh_worker.py tests/test_api_health.py tests/test_operations_scripts.py tests/test_api_system_ops.py
docker compose exec -T web npm run lint -- --quiet
docker compose exec -T web npm run build
```
