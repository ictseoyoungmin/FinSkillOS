# 132 — Collection Control Confirm + Undo (idea U9)

**Status:** Done. Frontend-only safety polish on the Collection Control surface.

Promotes ideas-backlog **U9** (confirm + undo on destructive removal).

## Implemented
- **Inline two-step confirm on folder delete** — the Delete button first arms an
  inline "Delete this folder? · Confirm · Cancel" row (`confirmingDelete` state)
  so a folder and its members are never dropped on a single misclick. Confirm
  commits; Cancel resets. System folder stays protected (button disabled).
- **Undo on ticker removal** — removing a ticker now shows an "Undo" action in the
  notice that re-adds the ticker (`addFolderSymbol`). The panel notice gained an
  optional `undo` action threaded through the shared mutation.

## Files
- `frontend/src/features/collection-control/components/CollectionControlPanel.tsx`
  — `PanelNotice` type with optional `undo`; mutation input carries `undo`;
  `onRequestDeleteFolder` (two-step) replaces the direct delete; `onRemoveSymbol`
  attaches an Undo; FolderCard renders the confirm/cancel pair + the notice renders
  the Undo button. New testids: `collection-delete-confirm-<id>`,
  `collection-delete-cancel-<id>`, `collection-control-undo`.
- `frontend/src/pages/system-ops/system-ops.css` — undo / confirm / cancel styles.

## Verification
- `npm run build` (tsc -b + vite) PASS; `npm run lint` clean (pre-existing
  ThemeProvider warning only).
- Docker: `docker compose build web` (production image) PASS.
- No backend/API/test surface touched — offline pytest suite unaffected.

## Note
- Undo for folder *delete* is intentionally not offered (a cascade re-create is
  fragile); the two-step confirm covers that more-destructive case instead.
- Visual baseline regen for `system-ops.png` is still the standing W-4 follow-up
  (needs browsers).
