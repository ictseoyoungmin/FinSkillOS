# 121 — Top Navigation Scanability

Date: 2026-06-02

## Goal

Close D-005 from `.devmd/PROJECT_DIAGNOSTICS.md`: the OS top tray should make
all 10 modules easier to scan at the desktop audit viewport and should use the
module-specific identity already present in `nav-config.ts`.

## Scope

- Keep the existing top-level routes and command palette labels.
- Use compact visible labels in the tray while preserving full accessible module
  names.
- Use the configured `iconChar` values instead of the generic nav dot.
- Validate no top-tray overflow at the 1280px audit width.

## Implemented

- Added `shortLabel` to `OS_NAV_ITEMS`.
- Updated `OsTopTray` nav links to render `iconChar` plus `shortLabel`, with the
  full module name retained as `aria-label`.
- Tightened `os-tray.css` nav button sizing with equal-width compact buttons and
  removed the generic dot styling.
- Expanded `frontend/e2e/navigation.spec.ts` to verify tray icons and no tray
  overflow at 1280px.
- Updated `.devmd/PROJECT_DIAGNOSTICS.md` and `.devmd/CURRENT_STATE.md` so
  D-005 is recorded as complete.

## Tests

- `frontend/e2e/navigation.spec.ts` checks each tray link exposes the full
  module `aria-label`, renders its module-specific icon, and fits in the tray at
  1280px.
- `frontend/e2e/responsive.spec.ts` keeps the existing tray/workspace overflow
  smoke at desktop and narrow viewports.

## Verification

Docker verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/navigation.spec.ts e2e/responsive.spec.ts --project=chromium --workers=1
```

Results:

- Web image build: passed.
- Frontend production build/type validation: passed.
- Focused navigation/responsive Playwright suite: 11 passed.

## Known Issues

- D-007 through D-010 remain queued in `.devmd/CURRENT_STATE.md`.
