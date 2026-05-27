# 34 — Foldered Symbol Subscriptions / Watchlist Organization

## Goal

Promote the existing flat `symbol_subscriptions` list into a usable
watchlist organization layer. Users should be able to keep active
subscriptions grouped into named folders without changing the refresh
universe semantics.

## Product Role

- `symbol_subscriptions.active` remains the durable refresh-universe
  membership used by System Ops, worker refresh, and news feed policy.
- Folders are an organization layer for humans, not a trading signal and
  not an execution control.
- Folder membership must not delete stored bars, indicators, news, or
  subscription history.

## Scope

### Backend

- Add durable folder tables:
  - `symbol_subscription_folders`
  - `symbol_subscription_folder_memberships`
- Add repository helpers for:
  - list folders with active subscription members
  - create/upsert folder by name
  - assign subscribed ticker to folder
  - remove ticker from folder
- Add FastAPI read/write endpoints:
  - `GET /api/symbol-lab/subscription-folders`
  - `POST /api/symbol-lab/subscription-folders`
  - `POST /api/symbol-lab/subscription-folders/{folderId}/symbols/{ticker}`
  - `DELETE /api/symbol-lab/subscription-folders/{folderId}/symbols/{ticker}`

### Frontend

- Surface folders on Symbol Lab as a compact organization panel.
- Keep the current Subscribe / Unsubscribe workflow intact.
- Allow assigning the currently loaded ticker to a folder from the panel.

## Out Of Scope

- Broker/watchlist sync.
- Provider logo/image fetching.
- Folder-level refresh enable/disable.
- Trading actions or directional recommendations.

## Acceptance

- Existing active subscription behavior remains unchanged.
- Folder APIs are DB-backed and fixture-safe.
- Folder membership only accepts normalized uppercase subscribed tickers.
- React build and lint pass.
- Focused API tests cover create/list/assign/remove behavior.

## Completion Note — 2026-05-26

Status: DONE_AS_FOLDERED_SUBSCRIPTIONS_V0

Implemented:

- Added `symbol_subscription_folders` and
  `symbol_subscription_folder_memberships` via Alembic revision
  `0009_symbol_subscription_folders`.
- Added folder ORM models and `SymbolSubscriptionFolderRepository`.
- Added Symbol Lab folder API endpoints for list/create/assign/remove.
- Added React Symbol Lab `Subscription Folders` side-panel.
- Existing Subscribe / Unsubscribe and worker refresh-universe behavior
  remains based on `symbol_subscriptions.active`.

Tests:

- `tests/test_api_symbol_lab.py`
- `tests/integration/test_db_migrations.py`
- `ruff` focused checks for changed Python files.
- `web npm run lint -- --quiet`
- `web npm run build`

Notes:

- Folder membership hides inactive subscriptions in read responses.
- Assigning a ticker to a folder requires an active subscription first.
- No external logo/watchlist provider or broker sync was introduced.
