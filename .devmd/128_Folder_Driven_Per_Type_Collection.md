# 128 — Folder-Driven Per-Type Collection Sets (W-2)

**Status:** Done.

W-2 of folder-driven collection control. Makes the worker's collection universe
follow the per-folder flags introduced in slice 127, so each collection type
(market / indicator / news) tracks a different ticker set driven by the GUI.

## Implemented
- **`build_watchlist_refresh_policy(..., collection_type=...)`** — new optional
  `collection_type` of `"market" | "indicator" | "news"`. When given, the universe
  is `base_tickers ∪ {members of every is_active folder whose matching type flag
  (`track_market` / `track_indicators` / `track_news`) is on}`. Inactive folders
  and folders with the flag off contribute nothing. `scope` is reported as
  `collection:<type>` and the new `collection_type` field is set. `_COLLECTION_FLAG`
  maps type → flag; `_flagged_folder_tickers` does the filtered union.
- **Backward compatible** — `collection_type=None` (default) keeps the legacy
  active-subscription / named-folder behavior, so the read-only API routes
  (market_kernel, symbol_lab, system_ops) are unchanged. New dataclass field has a
  default, so no construction site breaks.
- **Worker wiring** (`scripts/refresh_worker.py::run_cycle`) — the market,
  indicator, and news policy builds now pass their respective `collection_type`.
  Per-type scope (`collection:market` …) flows into the worker-cycle audit row.

## Design note
- A ticker's **effective collection** is folder-membership-driven now: an active
  subscription that belongs to no active folder is *not* collected (the user's
  "add NVDA to a folder → tracked" model). The install-default System folder
  (slice 127) covers the 22 sector leaders out of the box, and the env base lists
  remain unioned into market/indicator during the transition, so nothing the
  default install collected regresses. News has no base list, so news collection
  is fully folder-driven (System folder seeds it).

## Tests
- `tests/test_watchlist_refresh_policy.py` (+4): base ∪ flagged members union,
  inactive-folder exclusion, per-type flag (`track_news=False` drops a folder from
  the news set but not the market set), and empty/no-folder → base only.

## Verification
- Offline: `test_watchlist_refresh_policy`, `test_operations_scripts`,
  `test_worker_jobs`, `test_news_feed_policy`, `test_api_market_kernel`,
  `test_api_symbol_lab`, `test_folder_collection_flags` PASS; ruff clean.
- Docker: `docker compose run --rm --no-deps api` pytest (policy + ops scripts +
  worker jobs + news feed) + ruff PASS.

## Follow-ups
- W-3: `/api/system-ops/collection-control` GET/PATCH + folder/symbol CRUD so the
  GUI can toggle the flags this slice now consumes.
- W-4: Ops Collection Control surface; remove runtime-settings ticker text fields.
- (Idea U1/U7) Symbol-Lab "add to folder" so subscribing also folders a ticker,
  and per-folder coverage chips.
