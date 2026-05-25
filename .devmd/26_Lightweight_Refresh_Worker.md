# 26 — Lightweight Refresh Worker

Status: `DONE`
Date: `2026-05-25`

## Goal

Add an optional local background process that keeps DB-backed market evidence
fresh without introducing Celery, Redis, or a production queue.

## News Provider Decision

Reference assets were checked for non-Naver news implementations. The only
clear live news implementation was `investment-bite-main`, which uses Naver
Search API plus optional AI enrichment and static JSON fallback.

No alternate provider implementation was found that is ready to reuse.
Therefore news refresh is deferred to a later crawling/provider design slice.

## Boundary

Allowed:

- Add a Docker Compose `worker` profile.
- Run market refresh followed by indicator calculation on an interval.
- Keep mock market refresh as the offline-safe default.
- Allow Yahoo only through explicit env configuration.
- Expose environment knobs for interval and enabled stages.

Not allowed:

- Add Redis, Celery, APScheduler, or a queue.
- Add news crawling in this slice.
- Fetch provider data during normal product page rendering.
- Add brokerage, order, or execution workflows.

## Runtime Contract

```text
docker compose --profile worker up -d worker

worker loop:
  refresh_market_data
  calculate_indicators
  sleep FINSKILLOS_WORKER_INTERVAL_SECONDS
```

Environment knobs:

```text
FINSKILLOS_WORKER_INTERVAL_SECONDS=86400
FINSKILLOS_WORKER_RUN_ON_START=1
FINSKILLOS_WORKER_MARKET_ENABLED=1
FINSKILLOS_WORKER_INDICATOR_ENABLED=1
FINSKILLOS_WORKER_PERSIST_INDICATOR_HISTORY=0
```

## Completion

- `scripts/refresh_worker.py` runs one cycle or a resident interval loop.
- `docker-compose.yml` exposes an optional `worker` profile.
- `.env` and `.env.example` document worker controls.
- Scheduler/refresh policy now records the optional lightweight worker while
  keeping news refresh deferred.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_operations_scripts.py -q  # 8 passed
python3 -m ruff check scripts/refresh_worker.py tests/test_operations_scripts.py  # passed
python3 scripts/refresh_worker.py --help  # passed
docker compose --profile worker config  # passed
docker compose --profile worker run --rm worker python scripts/refresh_worker.py --once  # status OK; 12 indicator snapshots written
git diff --check  # passed
```
