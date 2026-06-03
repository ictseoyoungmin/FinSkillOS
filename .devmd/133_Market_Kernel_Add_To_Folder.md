# 133 — Market Kernel "Add to Folder" (idea U1)

**Status:** Done. Frontend-only cross-link.

Promotes ideas-backlog **U1** ("add-to-folder from any tab"). Symbol Lab already
has a folders panel (`SymbolSubscriptionFoldersPanel`) over the same underlying
folders, so the remaining gap was **Market Kernel**, which had no folder
affordance.

## Implemented
- **`AddToCollectionFolder` reusable component**
  (`features/collection-control/components/AddToCollectionFolder.tsx`) — a compact
  "Track in [folder ▾] [Add]" control. Backed by the collection-control API, which
  **subscribes the ticker and links it to the chosen folder in one call**, so a
  symbol on screen becomes worker-tracked in a single click (works even if the
  ticker was never subscribed). Shows a tone-coded confirmation; the button reads
  "In folder" (disabled) when the ticker is already a member; resets on symbol
  change. Writes the returned snapshot to the shared `["collection-control"]`
  cache so the Ops Collection Control surface updates immediately.
- Wired into the **Market Kernel** toolbar (next to the timeframe tabs), bound to
  `payload.header.ticker`. Testids: `add-to-folder`, `add-to-folder-select`,
  `add-to-folder-button`, `add-to-folder-note`.
- CSS in `market-kernel.css`.

## Why a new component (not the Symbol Lab panel)
- Symbol Lab's existing panel uses `/symbol-lab/subscription-folders` which
  requires the ticker to already be an active subscription. The new component uses
  the collection-control add endpoint (subscribe + link), which is the right
  "one-click track" behavior for an arbitrary on-screen symbol. Both target the
  same folder rows, so the two surfaces stay consistent.

## Verification
- `npm run build` + `npm run lint` clean (pre-existing ThemeProvider warning only).
- Docker: `docker compose build web` PASS.
- The two API calls it makes (collection-control GET + add-symbol subscribe/link)
  were already live-verified in slices 129/131; no new backend surface.

## Follow-up
- F3 (slice 134): per-folder "refresh now" so a freshly folder-tracked symbol can
  be collected on demand rather than waiting for the next worker cadence.
