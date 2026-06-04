# 162 — Journal Templates / Review Prompts (Phase 3)

**Status:** Done. Closes Phase 3 (portfolio / journal real-use input).

The content layer for the journal: quick-fill **entry templates** that scaffold a
reflection entry, and **review prompts** — guiding questions for the weekly
review. All descriptive process copy; no trade direction or execution wording.

## Implemented

### API (`api/schemas/trade_memory.py`)
- `TradeFormRules` gains `entry_templates: list[EntryTemplate]` and
  `review_prompts: list[str]` (default content via `_default_entry_templates` /
  `_default_review_prompts`). `EntryTemplate` carries a `label`, a descriptive
  `side`, and optional `strategy_type` / `mistake_tags` / `reason` / `thesis`
  scaffolds. Served on every `/trade-memory` payload (live + fixture); the
  copy passes the descriptive-only safety scan.

### Frontend
- `TradeEntryForm` gains an optional `templates` prop: a chip row above the form
  that pre-fills side / strategy / reason / thesis / mistake-tags (keeps the
  date + ticker the user typed). Omitted in fixture/offline mode.
- `ReviewPromptsPanel` — a local-state reflection checklist (`done/total` badge,
  strike-through on check); a working aid, not persisted. Rendered live-only on
  Trade Memory, beside the weekly review.
- Both are live-gated (the page passes templates / renders the panel only when
  `source === "live"`), so the fixture visual baseline is unchanged — the
  frontend fixture's `entryTemplates` / `reviewPrompts` are empty arrays.

## Tests (`tests/test_api_trade_memory.py`, +1)
- form rules carry ≥3 templates + ≥3 prompts, every template side is in the
  allowed vocabulary, "Exit review" template present, and the new copy contains
  no forbidden execution wording.

## Verification
- Offline: trade-memory + safety-language + v42 pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing ThemeProvider
  warning only).
- Docker: api pytest + ruff + web build.

## Notes
- No migration (static content on the existing form-rules payload).
- No Playwright regen — new UI is live-gated; fixture render unchanged.
- **Phase 3 complete** (157–162). Next per ROADMAP: Phase 4 interpretation engine.
