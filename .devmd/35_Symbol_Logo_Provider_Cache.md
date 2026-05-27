# 35 — Symbol Logo Provider Cache / Shared Ticker Identity

## Status

Completed.

## Intent

Promote the deferred symbol-logo slot from Slice 28 into a shared,
DB-backed provider cache that can be reused by Symbol Lab and News
Intelligence without coupling page rendering to external HTTP calls.

## Scope

- Add `symbol_logo_cache` table and repository.
- Add a shared logo identity resolver.
- Support Logo.dev ticker image URLs when `FINSKILLOS_LOGO_DEV_TOKEN` is set.
- Keep existing local initials as the fallback when no provider token exists.
- Surface the same ticker identity contract in:
  - `GET /api/symbol-lab`
  - `GET /api/news-intelligence`
- Render ticker logos/avatars in Symbol Lab, latest news rows, event-linked
  rows, holdings-relevant rows, and ticker entries in News Impact Map.
- Add `scripts/seed_symbol_logos.py` to warm the cache for Nasdaq-100 plus
  AI / aerospace-air / quantum ticker groups while skipping rows that are
  already cached.

## Notes

- The DB stores provider URL metadata only; no logo image bytes are stored.
- The Logo.dev token is treated as a publishable image token and is passed to
  the frontend as part of the image URL.
- Logo resolution is deterministic: first cached URL, then configured provider,
  then local fallback.
- The implementation avoids Clearbit-style unauthenticated logo URLs and keeps
  provider use explicit via environment configuration.

## Environment

```env
FINSKILLOS_LOGO_PROVIDER=logo_dev
FINSKILLOS_LOGO_DEV_TOKEN=
```

With the token blank, UI remains stable with local ticker initials.

## Cache Warmup

```bash
docker compose exec -T api python scripts/seed_symbol_logos.py --json
```

Default universe:

- Nasdaq-100 constituents (101 tickers because Alphabet has GOOG / GOOGL).
- Nasdaq-listed AI-adjacent tickers already relevant to the app universe.
- Nasdaq-listed aerospace / airline / space tickers.
- Nasdaq-listed quantum-computing-adjacent tickers.

The script validates the Logo.dev response as an image before storing the URL.
Existing cache rows are skipped unless `--force` is passed.

2026-05-27 run:

```json
{"cached": 0, "failed": 0, "failedTickers": [], "stored": 120, "total": 120}
```

Immediate rerun confirmed duplicate provider calls are avoided:

```json
{"cached": 120, "failed": 0, "failedTickers": [], "stored": 0, "total": 120}
```

## Verification

- `python3 -m ruff check ...`
- `python3 -m pytest tests/test_api_symbol_lab.py tests/test_api_news_intelligence.py`
- `python3 -m pytest tests/integration/test_db_migrations.py`
- `docker compose exec -T web npm run lint -- --quiet`
- `docker compose exec -T web npm run build`
