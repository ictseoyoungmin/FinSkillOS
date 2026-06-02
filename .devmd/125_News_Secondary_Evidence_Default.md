# 125 — News Secondary Evidence Default

Date: 2026-06-02

## Source Queue Item

D-010 in `.devmd/CURRENT_STATE.md`:

> News Intelligence secondary evidence default — Decide whether lower secondary
> evidence should open by default, preview key rows, or show a stronger
> collapsed summary for top-to-bottom review.

## Scope

- Make the News Intelligence secondary evidence area visible during a normal
  top-to-bottom page review.
- Keep the existing `details` affordance so operators can still collapse the
  section if they want a shorter page.
- Do not alter news scoring, API contracts, article summaries, or descriptive
  safety wording.

## Implementation

- `frontend/src/features/news/components/NewsEvidenceDetails.tsx`
  - Added an optional `testId` prop for stable e2e assertions on the `details`
    element.
- `frontend/src/pages/news-intelligence/NewsIntelligencePage.tsx`
  - Set the Secondary Evidence details region to `defaultOpen`.
  - Added `data-testid="news-secondary-evidence"`.
- `frontend/e2e/news-events-memory.spec.ts`
  - Added coverage that the Secondary Evidence region is open by default and
    that holdings-relevant and event-linked evidence panels are visible.
  - Pinned the read-only News/Catalyst/Trade smoke assertions to fixture
    snapshot APIs so they do not fail when the live DB has sparse evidence.

## Verification

Docker checks:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/news-events-memory.spec.ts --project=chromium --workers=1
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/diagnostics/full-scroll-diagnostics.spec.ts --project=chromium --workers=1
```

## Result

- Web image build: passed.
- Frontend production build/type validation: passed.
- News/Catalyst/Trade Playwright suite: 7 passed.
- Full-scroll diagnostic Playwright suite: 10 passed.

## Notes

- This is the final queued diagnostic item in `.devmd/CURRENT_STATE.md`.
