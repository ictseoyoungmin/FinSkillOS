# Folder-Driven Collection Control — Ideas Backlog

> Running list of usability / feature ideas spun out while building the
> folder-driven collection control (see `COLLECTION_CONTROL_SPEC.md`). Keep
> adding as ideas surface; promote the good ones into the Work Queue.

Created 2026-06-02.

## Usability

- **U1 · Add-to-folder from any tab** — a quick "★ add to folder" affordance on
  Market Kernel / Symbol Lab so a ticker on screen can be tracked in one click.
- **U2 · Symbol search in Ops** — reuse the Symbol Lab search to add tickers by
  name/symbol with logo + identity, instead of typing a raw ticker.
- **U3 · Per-folder open/collapse + "focus mode"** — collapse all but one folder
  to control a single group without scrolling.
- **U4 · Bulk / global toggles** — one switch to enable/disable a collection type
  across every folder; "pause all collection" master switch.
- **U5 · Drag-and-drop** tickers between folders; multi-select chips.
- **U6 · Folder templates** — one-click presets ("Mega-cap tech", "Semis",
  "Macro proxies", "My watchlist") that create a folder pre-filled.
- **U7 · Coverage / freshness chip per folder** — "12/14 have stored bars · last
  refresh 2h ago", so the operator sees what's actually collected.
- **U8 · Provider-load hint** — show member count and a soft warning past a
  threshold (more tickers = more provider calls / slower cycles).
- **U9 · Confirm + undo** on destructive folder/ticker removal (snackbar undo).

## Feature depth

- **F1 · Per-ticker collection override** — a chip in a folder can opt a single
  ticker out of one type (e.g., track price but not news for an index ETF).
- **F2 · Per-folder refresh cadence** — "Core" hourly vs "Watchlist" daily;
  worker reads each folder's interval. Pairs with the job queue (per-folder jobs).
- **F3 · Per-folder enqueue** — "Refresh this folder now" button enqueues a
  scoped worker job (`refresh_market` with a folder filter) instead of all.
- **F4 · News relevance scoping** — only collect news for tickers the operator
  cares about (folder `track_news`), reducing noise + RSS load.
- **F5 · Folder = lens** — let product tabs (Analysis, Catalyst) filter by folder
  so the cockpit can focus on one watchlist group.
- **F6 · System folder protection + reseed** — System folder is undeletable; a
  "reseed defaults" action restores the sector-leader set if edited.
- **F7 · Collection audit** — record which folder/flag drove each worker job
  (already partially via job payload) and surface per-folder last-collected.
- **F8 · Import/export folders** — CSV/JSON export of folder + flags for backup
  or sharing (mirrors the Trade Memory CSV export pattern).

## Risk / safety

- **R1 · Mock-adapter guard** (done in Slice 126 polish) — extend: warn when a
  folder is active but the global adapter is `mock`.
- **R2 · Empty-state honesty** — a folder with all types off, or no members,
  should read as explicitly "not collecting", not silently idle.
- **R3 · Descriptive-only** — all folder/collection copy stays descriptive; no
  buy/sell/execution wording (hard constraint).

## Promoted to Work Queue
- (none yet — W-1…W-5 are the spec's base plan; promote ideas as slices land)
