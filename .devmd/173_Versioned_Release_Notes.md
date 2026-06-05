# 173 — Versioned Release Notes / CHANGELOG (Phase 5)

**Status:** Done. **Closes Phase 5 (personal deployment / packaging).**

Turns the `NN — Title` slice-commit convention into versioned release notes, and
captures the phase history in a curated changelog.

## Implemented

### `CHANGELOG.md` (repo root)
- Curated, phase-versioned: v0.5 Phase 5 (169–173) · v0.4 Phase 4 · v0.3 Phase 3 ·
  v0.2 Phase 2 · v0.1 Phase 1 · v0.0 foundations. States the descriptive-only
  product boundary; points at `.devmd/COMPLETED_SLICES.md` for the full history.

### `scripts/release_notes.py`
- `parse_slice_commits(subjects)` — pure parser of `NN — Title` commit subjects
  (drops non-slice commits, dedupes on number, ascending). `collect_subjects`
  reads `git log --format=%s <from>..<to>`. `render_markdown` emits the slice
  list. `--from` / `--to` (git refs) / `--version` / `--json` / `--help`.
- `fsoctl.sh release-notes` wraps it.

### Docs
- README/runbook reference the changelog + generator (see CHANGELOG.md header).

## Tests (`tests/test_operations_scripts.py`, +3 · `--help` contract +1)
- `parse_slice_commits` keeps `[169, 172, 173]` from a mixed subject list and
  drops non-slice commits; `render_markdown` shape; `CHANGELOG.md` exists and
  names each phase.

## Verification
- Offline: operations pytest PASS; ruff clean; `bash -n fsoctl.sh`; manual
  `./fsoctl.sh release-notes --from <ref>`.
- Docker (rebuilt api image): operations pytest + ruff.

## Notes
- No app / schema change. `release_notes.py` reads `git log` only (read-only).
- **Phase 5 complete (169–173):** operator CLI · migration safety check ·
  backup-restore drill · data-dir policy / release profile · versioned release
  notes. Next per ROADMAP: Phase 6 (optional automation / reports / alerts).
