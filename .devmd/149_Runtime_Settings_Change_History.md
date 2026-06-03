# 149 — Runtime Settings Change History (Phase 1)

**Status:** Done. The S5 (slice 143) follow-up: per-change history + one-click revert.

S5 surfaced only the overlay's *last-change* metadata (the overlay is a single
document). This adds an append-only change log and a revert affordance.

## Implemented
- **Schema/migration** — new `system_ops_settings_history` table (id, setting_key,
  old_value, new_value, updated_by, created_at) + migration
  `0018_settings_history` (`create_table` — portable across SQLite/Postgres).
- **Repo** — `SystemOpsSettingsRepository.patch` now diffs each key and writes a
  history row per *actual* change (no-op edits are skipped, so the log has no
  noise); `new_value=None` means reverted to the `.env` default. Added
  `list_history(limit)`.
- **API** — `runtime_overlay_meta` includes `history` (newest first); schema
  `SystemOpsRuntimeSettings.history: list[RuntimeSettingChange]`. New
  `POST /api/system-ops/runtime-settings/reset` reverts **all** overrides to
  `.env` (patches each key to None, each logged) — the one-click revert.
- **Frontend** — the Runtime Settings tab shows a "Change history" list (key,
  old→new, when, by) and a "Reset all to defaults" button (shown only when
  overrides exist).

## Tests
- `tests/test_api_system_ops.py`: a PATCH logs old→new (newest first), a repeated
  same-value PATCH adds no history, and reset reverts all overrides
  (`overrides == {}`, `updatedAt is None`) while logging the revert (222 → null).

## Verification
- Offline: system-ops + migration smoke (SQLite) PASS; alembic single head 0018;
  ruff clean; frontend build + lint clean.
- Docker: Postgres `migrate` applied 0018; SQLite alembic smoke + system-ops +
  market-data pytest + ruff PASS. (Both dialects per the migration checklist.)

## Note
- Value column is `String(512)` — comfortably holds the longest allow-listed
  setting (a 22-ticker CSV ≈ 150 chars). Per-key inline revert (vs reset-all) is a
  possible future refinement; reset-all + history covers the S5 ask.
