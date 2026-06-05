# 185 — Reusable Pagination for Long Lists (v3 Phase 8)

**Status:** Done. Applies pagination to the unbounded lists so tabs don't grow
without limit (user: "pagination이나 기타 테크닉을 적용할 수 있는 것들은 모두
적용하고").

## Implemented

### Shared
- `frontend/src/shared/hooks/usePagination.ts` — `usePagination(items, pageSize)`
  → `{ visible, page, pageCount, prev, next, setPage }`; resets to page 0 when the
  list size changes.
- `frontend/src/shared/ui/Pagination.tsx` — a shared Prev / `n / N` / Next pager
  (renders nothing for a single page). Exported from `shared/ui`.

### Applied (unbounded / growing lists)
- **Trade Memory** `RecentEntriesTable` — 10 / page (journal grows over time).
- **Catalyst** `EventRiskTable` — 8 / page (used for Upcoming / High-Risk /
  Holdings-Linked).
- **Catalyst** `EventLinkedNewsPanel` — 6 / page.
- **Risk** `ActiveAlertsTable` — 8 / page.
- News Intelligence already paginates via `PaginatedNewsList`.

CSS-only chrome + a slice of the list — no data/contract change.

## Verification
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt web image): web build.

## ⚠ Visual baselines
The paginated panels now show ≤ page-size rows + a pager → drifts those tabs'
`@visual` baselines; the user regenerates.

## Notes
- System Ops protocol-run history is server-limited + already a 2-col grid (184),
  so it isn't paginated. Symbol Lab recent-bars already has a max-height scroll.
- Page sizes are conservative; tune per the user's preference after viewing.
