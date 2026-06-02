# 127 — Folder Collection Flags + System-Folder Seed (W-1)

**Status:** Done.

First implementation slice of the folder-driven collection control feature
(spec: `docs/COLLECTION_CONTROL_SPEC.md`, ideas: `docs/COLLECTION_CONTROL_IDEAS.md`).
Lays the data + seed foundation; worker/API/frontend follow in W-2…W-5.

## Implemented
- **Schema** — five collection-control columns on `symbol_subscription_folders`:
  `is_active`, `track_market`, `track_indicators`, `track_news` (default `true`),
  `is_system` (default `false`). Migration `0016_folder_collection_flags`
  (down_revision `0015_system_ops_settings`). `SYSTEM_FOLDER_NAME = "System"`
  constant exported from the models package.
- **Repository** (`SymbolSubscriptionFolderRepository`) —
  `set_collection_flags(...)` (partial update; `None` leaves a flag as-is, raises
  `folder_not_found` for unknown ids), `ensure_system_folder(...)` (idempotent
  get-or-create, re-asserts `is_system` without disturbing operator-set flags),
  `has_member(folder_id, ticker)`, `member_count(folder_id)`. Snapshot dataclass
  gained the five flag fields and `list_snapshots` populates them.
- **Seed** — `seed_system_folder(session)` ensures the protected System folder and
  subscribes/links the 22-ticker `DEFAULT_US_TICKER_UNIVERSE` (source `system`),
  all collection types on. Returns counts (`created_folder` / `subscribed` /
  `linked` / `members`). Idempotent: re-run never duplicates rows and preserves
  operator-adjusted flags. Wired into `scripts/seed_sample_data.py` so a fresh
  install ships the System folder.
- **Protocol** — `POST /api/system-ops/seed-system-folder` (`seed_system_folder`
  key) + catalogue card; idempotent, descriptive copy.

## Tests
- `tests/test_folder_collection_flags.py` (8 tests): flag defaults, partial
  `set_collection_flags`, unknown-folder guard, `ensure_system_folder` idempotency
  + operator-flag preservation, seed registers full universe, seed idempotency
  (no duplicate System folder / zero re-subscribe), snapshot flag exposure.
- `ProtocolKey` literal extended with `seed_system_folder`.

## Verification
- Local offline: `test_folder_collection_flags` + `test_watchlist_refresh_policy`
  + `test_api_symbol_lab` + `test_operations_scripts` PASS; ruff clean on all
  changed files; `alembic heads` single (`0016…`).
- Docker: `docker compose run --rm migrate` applied `0015 → 0016` against
  Postgres cleanly; `docker compose run --rm --no-deps api python -m pytest
  test_folder_collection_flags test_api_system_ops test_watchlist_refresh_policy
  test_api_v42_contract` — all pass **except** the pre-existing
  `test_system_ops_get_returns_full_payload`, which fails identically on a clean
  tree (confirmed by `git stash` + re-run). It is a slice-112 isolation-fixture ×
  Docker-psycopg interaction (see Known issues), not introduced by this slice.

## Notes
- A folder's **effective collection set** = union over its `is_active` folders'
  matching type flag — consumed by W-2 (worker per-type ticker sets).
- Migration adds the columns only; ticker choice stays in code (the seed protocol
  fills the folder), so the install universe is editable without a migration.

## Known issues / follow-ups
- **Pre-existing (not W-1):** under Docker (psycopg installed) the slice-112
  autouse isolation fixture points `DATABASE_URL` at an unreachable host, so
  `get_session_scope()` raises `OperationalError` at connect time *before* the
  `if session is None` offline guard in the `GET /api/system-ops` route — failing
  `test_system_ops_get_returns_full_payload`. Locally (no psycopg) the same path
  raises `ModuleNotFoundError`. Fix candidate: have `get_session_scope()` yield
  `None` on connection failure (treat unreachable == offline) so the isolation
  fixture degrades gracefully regardless of driver presence. Tracked separately.
- W-2: `build_watchlist_refresh_policy` per-type ticker sets + worker wiring.
- W-3: `/api/system-ops/collection-control` GET/PATCH + folder/symbol CRUD.
- W-4: Ops Collection Control surface; remove runtime-settings ticker text fields.
