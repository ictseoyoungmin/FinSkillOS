# 141 — Collection Refresh Semantics Copy (S6)

**Status:** Done. Frontend copy-only.

Per the 2026-06-03 review (S6): a per-folder "Refresh now" collects **only that
folder's members** — it does not union the global base universe and excludes
inactive folders / disabled collection types (the F3 design). Without explicit
copy an operator could read it as a global refresh and ask "why didn't my other
tickers update?".

## Changes (`CollectionControlPanel.tsx`)
- Success notice now states the scope: `Refresh queued for "<folder>" — this
  folder's symbols only, not the global universe.`
- The "Refresh now" button tooltip spells out the semantics: only this folder's
  symbols, not the global universe; excludes disabled types; an inactive folder
  collects nothing.

## Verification
- `npm run build` + `npm run lint` clean (pre-existing ThemeProvider warning only).
- Docker: `docker compose build web` PASS.
- No backend/test surface touched.

Backlog: `workflow_and_memory/project_stabilization_backlog_2026_06_03.md`.
