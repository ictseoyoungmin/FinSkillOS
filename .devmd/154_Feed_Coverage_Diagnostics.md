# 154 — News / Event Feed Coverage Diagnostics (Phase 2)

**Status:** Done. Read-only. Last read-only Phase-2 slice before the 155 data-repair
(which is confirmed with the operator first).

Lets an operator tell whether a thin News / Catalyst tab is a *feed gap* (nothing
ingested / stale) rather than a quiet market.

## Implemented
- **Repos**: `NewsArticleRepository.{count, count_since, latest_published_at,
  source_counts}` and `EventRepository.{count, count_upcoming, latest_start_date,
  source_counts, date_status_counts}`.
- **API** — `GET /api/system-ops/feed-coverage` → `FeedCoverageReport`:
  - `news`: totalArticles, latestPublishedAt, recentArticles (7d), freshnessStatus
    (FRESH ≤3 days / STALE / EMPTY), source distribution.
  - `events`: totalEvents, upcomingEvents, latestEventDate, source + date-status
    distribution.
  - readable `detail`. `session is None` → db-unavailable shape.
- **Frontend** — a "Feed Coverage" panel in System Ops → Worker Status (own query):
  news freshness badge, detail line, and a News / Events grid with counts + source
  breakdowns.

## Tests
- `tests/test_api_system_ops.py`: 2 news articles (1 recent) + 1 upcoming event →
  totalArticles 2, recentArticles 1, freshness FRESH, news source MockWire, events
  total/upcoming 1, date-status includes TENTATIVE.

## Verification
- Offline: system-ops + v42 contract + news + event tests PASS; ruff clean; frontend
  build + lint clean.
- Docker: api pytest + ruff + build api/web.

## Phase 2 read-only trio complete (151–154)
Provider health · provenance · invariants · feed coverage — the "why is the data in
this state" surface. **155 (Data Repair / Quarantine) is data-mutating** — its scope
(synthetic bars from 152, orphan snapshots from 153), dry-run, and confirm policy
are agreed with the operator before building.
