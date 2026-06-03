# 143 — Runtime Settings Change Audit (S5)

**Status:** Done.

Per the 2026-06-03 review (S5): the runtime-settings overlay is powerful (a bad
value persists across restarts), so who/when last changed it must be visible.

## Findings (audit of the existing overlay)
- The `system_ops_settings` row already stores `updated_at` + `updated_by` (set to
  `system_ops_api` by the PATCH endpoint), and **per-key rollback already exists**:
  `SystemOpsSettingsRepository.patch` pops a key when its value is `None`, reverting
  it to the `.env` default.
- **Gap:** none of that metadata was surfaced — the GET response only returned
  `values` / `overrides` / `captured_at` (= now), so the cockpit couldn't show who
  or when. Allow-list + typed validation are already strict (PATCH rejects unknown
  keys with 400) — confirmed, unchanged.

## Implemented
- `runtime_overlay_meta` now includes `updated_at` + `updated_by` (via a new
  `_read_overlay_audit(session)` that mirrors the override-read session handling;
  returns `(None, None)` when nothing is overridden or offline).
- Schema `SystemOpsRuntimeSettings` gains `updated_at` / `updated_by`.
- Ops Runtime Settings tab renders a "last changed" line: "N overrides active ·
  last changed <when> by <who>" (amber when overrides exist), or "No overrides —
  all settings use .env defaults." (`data-testid="system-ops-runtime-audit"`).

## Tests
- `tests/test_api_system_ops.py`: empty overlay → null audit; after a PATCH the
  `updatedAt` / `updatedBy` are populated on both the PATCH and GET responses.

## Verification
- Offline: system-ops tests PASS; ruff clean; frontend `npm run build` +
  `npm run lint` clean.
- Docker: api pytest + `build api web` PASS.

## Scoped out (follow-up)
- Full per-change **history** (each PATCH as an audit row) + one-click revert UI.
  The single-row overlay only carries last-change metadata; per-key revert exists
  in the repo (`value=None`) but isn't yet a UI affordance. Tracked for a later
  slice if the operator wants a settings changelog.
