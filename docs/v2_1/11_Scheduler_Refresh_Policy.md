# 11. Scheduler / Refresh Policy

> Current status: v2.1 / v4.2 local operations policy.
> This document defines the refresh contract. The default remains
> manual-first, with an optional lightweight Docker worker for local
> continuous market/news/indicator refresh. Celery and Redis remain out of scope.

## 1. Operating Stance

FinSkillOS is a personal investment OS, not a trading robot. Refresh jobs
prepare evidence for interpretation; they do not trigger orders, execution,
or price-direction commands.

The default operating model is:

```text
manual-first
script-driven
cron-compatible
optional lightweight worker
System-Ops visible
status-endpoint observable
```

## 2. Refresh Ownership

| Data / state | Owner | Default trigger | Notes |
|---|---|---|---|
| Portfolio snapshot | user import / System Ops seed | manual | Real broker sync is out of scope. |
| Market bars | `scripts/refresh_market_data.py` / `scripts/refresh_worker.py` | manual, after-market cron, or worker interval | Uses configured adapter; mock is offline-safe. |
| Indicators | `scripts/calculate_indicators.py` / `scripts/refresh_worker.py` | after market bars | Computes descriptive snapshots only. |
| Market regime | `scripts/run_regime_scan.py` | after indicators | Persists read-only regime interpretation. |
| Risk guards | System Ops protocol | after portfolio/regime changes | Refreshes guard ladder / active alerts. |
| News | `scripts/refresh_news.py` / `scripts/refresh_worker.py` | manual, cron, or worker interval | RSS/Atom metadata only; no article body crawling/storage. |
| Events | manual entry / seed protocol | manual | Uncertain dates remain tentative/window/speculative. |
| Visual QA | Docker Playwright gate | before UI completion claims | Confirms product cockpit still renders correctly. |

## 3. Recommended Local Routine

After market close or before a review session:

```bash
python3 scripts/refresh_market_data.py --adapter mock
python3 scripts/calculate_indicators.py
python3 scripts/run_regime_scan.py
```

Then use System Ops to run risk guards if portfolio or regime state changed.

To run the optional lightweight worker in Docker:

```bash
docker compose --profile worker up -d worker
docker logs --tail 80 finskillos-worker
```

The worker runs this bounded sequence:

```text
refresh market bars
refresh news metadata when FINSKILLOS_NEWS_RSS_FEEDS is configured
calculate descriptive indicators
sleep FINSKILLOS_WORKER_INTERVAL_SECONDS
```

News refresh is RSS/Atom only at this stage. Feed URLs are supplied through
`FINSKILLOS_NEWS_RSS_FEEDS`; no bundled provider list, paid API adapter, or
linked article crawler is enabled by default.

For a cron-style local schedule, run the same commands in order and preserve
logs. Example timing is deliberately local and conservative:

```text
18:30 local market-data refresh
18:34 news metadata refresh
18:35 indicator compute
18:40 regime scan
manual guard refresh after portfolio review
```

## 4. Staleness Rules

`/api/system-status` is the operational source for freshness labels.

Each snapshot should expose:

```text
generatedAt
source
latestMarketBarAt
latestIndicatorAt
latestRegimeAt
latestNewsAt
latestEventAt
staleFlags
```

The React cockpit must show stale or missing state instead of presenting
fixture fallback as live data.

## 5. Failure Policy

Refresh commands should fail softly:

- A single ticker failure must not crash the whole market refresh.
- Missing bars should appear as indicator compute errors for that ticker.
- Regime scan may produce `UNKNOWN` when inputs are incomplete.
- Scripts should log summaries that can be copied into an operations note.
- No refresh command should mutate brokerage state or execution workflows.

## 6. Worker Policy

Do not add Celery, Redis, or APScheduler. The only approved resident process
at this stage is the optional Docker `worker` profile running
`scripts/refresh_worker.py`.

Escalate beyond the lightweight worker only when one of these needs is real:

- refreshes must continue while no terminal session is active;
- multiple users or machines need coordinated job state;
- job retries and audit state outgrow JSONL / logs;
- live adapters require rate-limit orchestration.

Until then, scripts plus System Ops protocols plus the optional worker are the
source of operational truth.
