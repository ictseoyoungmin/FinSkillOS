# 150 — Collection Control Operator Copy Polish (Phase 1)

**Status:** Done. Frontend copy-only. Closes Phase 1.

Continues S6 (slice 141, refresh-scope wording) with broader operator clarity on
the Collection Control tab, so the folder-flag model is self-explanatory.

## Changes (`CollectionControlPanel.tsx`)
- **Subtitle** now states the model: "the worker collects a symbol only while it is
  in an Active folder with the matching type enabled … an inactive folder — or an
  off type — collects nothing." (The earlier copy implied per-folder toggles
  without saying what off/inactive means.)
- **Totals** relabeled "Folders" → "Active folders" and each stat
  (Price/Indicators/News) gained a tooltip: "distinct symbols the worker collects
  … across active folders," so the counts read as effective collection, not raw
  membership.
- **Global toggles** label "All folders" → "Apply to all folders" (+ tooltip),
  making it an action rather than a heading.
- `CoverageStat` accepts an optional `hint` (title tooltip).

The W-5 inactive / all-types-off warnings and the S6 per-folder "this folder only"
refresh copy are unchanged and now reinforced by the subtitle.

## Verification
- `npm run build` + `npm run lint` clean (pre-existing ThemeProvider warning only).
- Docker: `docker compose build web` PASS.
- No backend/test surface touched.

## Phase 1 complete
145 runbook · 146 worker queue UI · 147 refresh explanation · 148 provider
retry/backoff · 149 settings history · 150 collection copy. Next: Phase 2
(data-trust / provider resilience — provider health dashboard, provenance).
