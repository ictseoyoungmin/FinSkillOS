# 129 — Collection Control API (W-3)

**Status:** Done.

W-3 of folder-driven collection control. The GUI-facing API that reads and
mutates the per-folder collection flags (slice 127) the worker now consumes
(slice 128). New router `api/routes/collection_control.py` + schemas
`api/schemas/collection_control.py`, mounted at `/api/system-ops/collection-control`.

## Endpoints
- **GET** `…/collection-control` — folders (System pinned first) with flags,
  members + member count, plus a `totals` roll-up: folder / active-folder counts,
  per-type effective ticker counts (`market` / `indicator` / `news`, computed with
  the same `build_watchlist_refresh_policy(collection_type=…)` the worker uses),
  and `*_all` flags that drive the global toggles. `source="live"`; descriptive
  `safetyCaption`.
- **POST** `…/folders` — create/upsert a folder.
- **PATCH** `…/folders/{id}` — partial flag update (`isActive` / `trackMarket` /
  `trackIndicators` / `trackNews`); unknown id → 404.
- **DELETE** `…/folders/{id}` — delete; the System folder is protected → 409
  (`system_folder_protected`); unknown id → 404.
- **POST** `…/folders/{id}/symbols` — `{ticker, name?}`: subscribes the ticker (if
  needed) and links it in one call (the GUI "add NVDA → tracked" flow).
- **DELETE** `…/folders/{id}/symbols/{ticker}` — unlink.
- **POST** `…/global-toggle` — `{flag, value}`: applies one flag to every folder.

All return the full refreshed `CollectionControlResponse` so the UI re-renders
from one payload. `session is None` (DB unavailable) → empty live shape with
`systemStatus.db="UNAVAILABLE"`, never fixture content.

## Supporting changes
- `SymbolSubscriptionFolderRepository.delete_folder(folder_id)` — cascade-deletes
  memberships, raises `system_folder_protected` for the System folder.
- `api/main.py` — registered the router; added `PATCH` to the CORS `allow_methods`
  so the browser preflight succeeds for flag updates.

## Tests
- `tests/test_api_collection_control.py` (9): System-first + flags shape, flag
  PATCH persistence (+ per-type count effect), folder create/delete, System-delete
  blocked (409), symbol add/remove, global toggle across all folders, unknown
  folder 404, descriptive-only copy, and well-formed empty shape.
- `tests/test_api_system_ops.py` — `_PROTOCOL_KEYS` + `_POST_ENDPOINTS` updated for
  the slice-127 `seed_system_folder` protocol.

## Verification
- Offline: full `pytest tests/` suite PASS (no failures); ruff clean.
- Docker: `docker compose run --rm --no-deps api` pytest (collection control +
  system ops + v42 contract + folder flags + watchlist policy) + ruff PASS.

## Follow-ups
- W-4: Ops Collection Control surface (folder cards + checkboxes + symbol search);
  remove the runtime-settings ticker text fields, pointing operators here instead.
- W-5: per-folder coverage/freshness chips, open/collapse focus, Symbol-Lab
  "add to folder" cross-link.
