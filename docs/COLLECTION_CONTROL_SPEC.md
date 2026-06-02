# Folder-Driven Collection Control — Spec

> Living spec. Update as the feature lands. Created 2026-06-02.

## Problem

Today the worker's collection universe is a **comma-separated text field** in the
Ops Runtime Settings (`FINSKILLOS_MARKET_REFRESH_TICKERS` /
`…_INDICATOR_REFRESH_TICKERS`). That is error-prone (manual typing), duplicated
across two keys, and disconnected from the existing **watchlist folder** feature.
Collection on/off is only a **global** env toggle
(`FINSKILLOS_WORKER_{MARKET,NEWS,INDICATOR}_ENABLED`), so an operator can't say
"track news for these tickers but not those".

## Goal

Make collection **GUI-driven and folder-based**:

- The install default ships sector leaders pre-registered in a protected
  **"System"** folder, so a fresh install already collects useful data — no text
  entry needed.
- Operators add/remove tickers via the GUI (reusing the existing folder /
  Symbol-Lab subscribe feature). Adding `NVDA` to a folder makes the worker track
  NVDA's price, indicators, and news and surface them across the cockpit.
- Each folder has **per-collection-type checkboxes** — Active, Price/Market,
  Indicators, News — controllable **globally or per folder**.
- The runtime-settings ticker text fields are removed (the universe is no longer
  hand-typed).

## Existing infrastructure (reuse)

- `SymbolSubscription` (ticker, `active`) — durable subscription universe.
- `SymbolSubscriptionFolder` (name, description, sort_order) +
  `SymbolSubscriptionFolderMembership` (folder ↔ subscription).
- `SymbolSubscriptionFolderRepository`: `upsert_folder`, `add_symbol`,
  `remove_symbol`, `list_snapshots`.
- `build_watchlist_refresh_policy(session, base_tickers, folder_names)` — already
  folder-aware (base ∪ active subscriptions, optional folder scope).
- Frontend `SymbolSubscriptionFoldersPanel`, `WatchlistCard`; Symbol Lab
  subscribe / unsubscribe.

## Design

### Data model
Add **per-folder collection flags** (`SymbolSubscriptionFolder`):

| Column | Default | Meaning |
|---|---|---|
| `is_active` | `true` | folder participates in collection at all |
| `track_market` | `true` | collect price/OHLCV bars for members |
| `track_indicators` | `true` | compute indicators for members |
| `track_news` | `true` | collect news for members |
| `is_system` | `false` | protected System folder (can't delete; flags still toggle) |

A ticker's **effective collection set** = union over the folders it belongs to
that are `is_active` and have the matching type flag. This gives folder-level
control with per-ticker membership granularity (the user's "add NVDA → tracked"
flow), plus global control (toggle every folder).

### Seed
A `seed-system-folder` System Ops protocol (idempotent) creates the **System**
folder (`is_system=true`) and subscribes the install default sector leaders
(the 22-ticker cockpit universe), all collection types on. Re-runnable; never
duplicates. (Migration seeds an empty System folder; the protocol fills it so
ticker choice stays in code, not a migration.)

### Worker
`build_watchlist_refresh_policy` gains **per-type ticker sets**:

- `market_tickers` = active-folder members with `track_market`
- `indicator_tickers` = active-folder members with `track_indicators`
- `news_tickers` = active-folder members with `track_news`

The worker's market / indicator / news refresh each use the matching set instead
of one flat universe. The global `FINSKILLOS_WORKER_*_ENABLED` flags remain as a
hard master switch (off → that type is skipped regardless of folder flags). Empty
set → that type NOOPs (no provider call).

### API
Reuse folder CRUD; add:

- `GET /api/system-ops/collection-control` — folders (System first) with flags,
  members, per-type effective ticker counts, and global roll-up.
- `PATCH /api/system-ops/collection-control/folders/{id}` — set
  `is_active` / `track_market` / `track_indicators` / `track_news`.
- `POST …/folders` (create), `DELETE …/folders/{id}` (non-system only).
- `POST …/folders/{id}/symbols` / `DELETE …/folders/{id}/symbols/{ticker}` —
  GUI add/remove (subscribes/links the ticker).
- Global toggles apply the flag to every folder in one call.

### Frontend (Ops)
Replace the runtime-settings ticker text fields with a **Collection Control**
surface (own tab or panel):

- Folder list (System pinned first), each a card with: name, member chips, and
  Active / Price / Indicators / News checkboxes.
- Add ticker (symbol search, reusing Symbol Lab search) / remove ticker chip.
- Create / rename / delete folder (System protected).
- A **global** row of the four toggles (apply to all folders).
- Per-folder open/collapse for focus.
- Live coverage hint per folder (how many members have stored bars / fresh data).

Runtime Settings keeps the **non-ticker** worker knobs (interval, poll, adapter,
news feed config). The two ticker text fields are removed.

## Out of scope (initial)

- Per-ticker (per-membership) collection override (folder-level is enough first).
- Per-folder refresh cadence (see ideas doc).

## Slice plan (W-series)

- **W-1** schema: folder collection flags + `is_system` + migration; repo
  setters; `seed-system-folder` protocol; tests.
- **W-2** worker: folder-driven per-type ticker sets in `watchlist_refresh_policy`
  + worker cycle wiring; tests.
- **W-3** API: collection-control GET / PATCH / folder+symbol CRUD + global
  toggles; tests.
- **W-4** frontend: Ops Collection Control surface; remove runtime-settings ticker
  text fields; wire add/remove + checkboxes.
- **W-5** polish: global toggles, open/collapse, Symbol-Lab "add to folder"
  cross-link, coverage hints, empty/MISSING states.

## Verification per slice

Offline pytest + ruff + Docker pytest; web build/lint; live demo (add a ticker to
a folder → worker collects it → tab shows it). No data duplication (upsert +
idempotent seed). Descriptive-only copy (no execution wording).
