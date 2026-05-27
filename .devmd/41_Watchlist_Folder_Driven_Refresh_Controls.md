# 41 — Watchlist Folder Driven Refresh Controls

## Goal

Promote subscription folders from organization-only UI into an optional
refresh-control layer for System Ops and the lightweight worker.

The system should:

- keep `symbol_subscriptions.active` as the default refresh universe;
- allow operators to scope refreshes to named watchlist folders;
- keep explicit env tickers as a stable baseline;
- use the same policy for market bars, indicators, and news feed generation;
- avoid deleting bars, indicators, news, logos, or subscription history.

## Design

Default behavior remains unchanged:

```text
explicit/default refresh tickers + all active subscriptions
```

When `FINSKILLOS_REFRESH_FOLDER_NAMES` is set to a comma/semicolon-separated
list of folder names, refreshes use:

```text
explicit/default refresh tickers + active members of matching folders
```

If the configured folders do not exist or have no active members, the policy
falls back to all active subscriptions. This keeps the worker predictable and
prevents an accidental empty folder from silently disabling refresh coverage.

## Implemented

- Added `finskillos.services.watchlist_refresh_policy`.
- Added a shared `WatchlistRefreshPolicy` DTO with ticker universe, scope, and
  diagnostic detail.
- System Ops market refresh now uses the folder-aware policy.
- System Ops indicator calculation now uses the folder-aware policy.
- System Ops news refresh now builds RSS query tickers from the same policy.
- Worker market/news/indicator cycles use the same folder-aware policy and add
  scope/folder metadata to cycle summaries.
- Tests cover default all-active behavior, named-folder scoping, and empty
  folder fallback.

## Out of Scope

- User-facing folder refresh buttons.
- Per-folder intervals.
- Folder-level enable/disable persistence.
- Broker/watchlist provider sync.

## Validation

```bash
python3 -m ruff check finskillos/services/watchlist_refresh_policy.py api/routes/system_ops.py scripts/refresh_worker.py tests/test_watchlist_refresh_policy.py tests/conftest.py
timeout 90 env FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_watchlist_refresh_policy.py tests/test_api_system_ops.py tests/test_operations_scripts.py -q
```
