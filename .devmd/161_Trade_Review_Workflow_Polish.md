# 161 — Trade Memory Review Workflow Polish (Phase 3)

**Status:** Done. Weekly-review period navigation — review completed past weeks,
not just the rolling window ending today.

The weekly review was hardcoded to the 7-day window ending today
(`ReflectionService.weekly_review` uses `start = today - 6d`). When you actually
sit down to review, you usually want *last* week. This slice lets the review step
back over completed weeks; the markdown export follows the selected week.

## Implemented

### API (`api/routes/trade_memory.py`)
- `GET /api/trade-memory/weekly-review?as_of=YYYY-MM-DD` — computes the 7-day
  window ending `as_of` via the same `ReflectionService.weekly_review(today=…)`
  engine + `render_weekly_review_markdown`, mapped through the existing
  `_weekly_review_from_vm`. No `as_of` (or an invalid date, or fixture mode) →
  the embedded current-week block, unchanged. Live-error / no-session fall back
  to the same error/db-unavailable weekly block as the rest of the route.
- New helper `_weekly_review_for_date(session, target_date)`. Stored entries were
  wording-scanned at write time, so the rendered markdown stays descriptive.

### Frontend
- `WeeklyReviewPanel` gains an optional `navigation` prop (live only): a
  prev / next / this-week stepper with a "N weeks ago" / "This week" label and a
  loading hint. Omitted in fixture/offline mode, so the static card (and the
  Playwright visual baseline) is byte-identical.
- `TradeMemoryPage` owns `weekOffset`: offset 0 renders the embedded weekly;
  a non-zero offset fetches `weekly-review?as_of=<endDate − offset·7d>`
  (react-query keyed on `as_of`, enabled only live) and feeds the result to BOTH
  the panel and the markdown export so they stay in sync. `fetchWeeklyReview`
  now takes an optional `asOf`.

## Tests (`tests/test_api_trade_memory.py`, +2)
- two entries 10 days apart: default window counts only the recent one;
  `?as_of=<10 days ago>` returns the older window (correct start/end dates);
- an invalid `as_of` falls back to the current week.

## Verification
- Offline: trade-memory + v42 + safety-language pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration. No Playwright regen — navigation is live-gated; fixture render
  unchanged.
- Next: 162 Journal Templates / Review Prompts (the review-prompt content layer).
