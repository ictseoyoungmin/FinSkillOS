# 32 — News RSS / Atom Provider Adapter

## Goal

Add the first non-mock news provider adapter while preserving the Slice 10
contract:

- no full article body storage;
- deterministic tests without live network calls;
- provider output normalized to `NewsArticleInput`;
- `NewsService` remains responsible for upsert, truncation, and classification.

## Scope

Implemented:

- `RssNewsAdapter` for RSS 2.0 and Atom feeds.
- `RssFeed` config object with optional source/language overrides.
- `NewsDataFetchError` for fetch/parse failures.
- HTML tag cleanup, whitespace cleanup, UTC datetime normalization, and defensive
  title/summary clipping to the existing DB caps.
- `scripts/refresh_news.py` for manual/cron-compatible RSS refresh.
- Local `--feed-file` mode for offline refresh/test runs.
- System Ops `refresh_news` protocol backed by `FINSKILLOS_NEWS_RSS_FEEDS`.
- React System Ops protocol types/path/fixture entry.
- `scripts/refresh_worker.py` now runs news metadata refresh during each cycle
  when `FINSKILLOS_WORKER_NEWS_ENABLED=1`.
- Unit tests using static RSS/Atom XML strings only.

Out of scope:

- bundled default feed URLs;
- scheduled crawling;
- paid/vendor APIs;
- full article crawling or body persistence;
- bundled feed provider policy.

## Files

- `finskillos/data_sources/news_adapter.py`
- `finskillos/data_sources/adapters/rss_news_adapter.py`
- `finskillos/data_sources/__init__.py`
- `scripts/refresh_news.py`
- `scripts/refresh_worker.py`
- `docker-compose.yml`
- `.env.example`
- `docs/v2_1/11_Scheduler_Refresh_Policy.md`
- `api/routes/system_ops.py`
- `api/schemas/system_ops.py`
- `api/fixtures/system_ops.py`
- `frontend/src/features/system-ops/api.ts`
- `frontend/src/features/system-ops/types.ts`
- `frontend/src/mocks/fixtures/systemOps.fixture.ts`
- `tests/test_news_rss_adapter.py`
- `tests/test_operations_scripts.py`
- `tests/test_api_system_ops.py`

## Validation

```bash
python3 -m pytest tests/test_news_rss_adapter.py tests/test_news_intelligence.py -q
python3 -m pytest tests/test_operations_scripts.py -q
timeout 60 python3 -m pytest tests/test_api_system_ops.py -q
timeout 60 python3 -m pytest tests/test_operations_scripts.py tests/test_api_system_ops.py tests/test_news_rss_adapter.py tests/test_news_intelligence.py -q
python3 -m ruff check finskillos/data_sources/news_adapter.py finskillos/data_sources/adapters/rss_news_adapter.py finskillos/data_sources/__init__.py tests/test_news_rss_adapter.py
docker compose exec -T web npm run lint -- --quiet
docker compose exec -T web npm run build
```

## Notes

- Network fetching is available through `urllib.request`, but tests inject a
  fetcher so CI/local validation remains offline-safe.
- The adapter stores source/title/link/published/short summary metadata only.
  It does not fetch linked article pages.
- Feed URL selection and refresh orchestration should be handled in a later
  System Ops or worker slice.
- `refresh_news.py --feed-file` exists so provider parsing and DB ingestion can
  be exercised without internet access.
- System Ops returns `NOOP` until `FINSKILLOS_NEWS_RSS_FEEDS` is configured.
- Worker behavior matches System Ops: with no RSS feeds configured, news is a
  `NOOP`; with feed URLs configured, the worker ingests metadata automatically.
- RSS adapter is intentionally imported from
  `finskillos.data_sources.adapters.rss_news_adapter` instead of re-exported
  through `finskillos.data_sources.__init__`; the news service depends on DB
  repositories, so a package-level re-export can create circular imports during
  repository collection.
