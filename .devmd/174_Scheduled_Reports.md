# 174 — Scheduled Daily/Weekly Report Generation (Phase 6)

**Status:** Done. Opens Phase 6 (optional automation / reports / alerts).

Writes a dated descriptive evidence report to `data/exports/`, so a cron / worker
cadence can keep daily + weekly reports on disk. Builds on the Slice-168 weekly
evidence report.

## Implemented

### `api/weekly_report.py`
- `build_daily_brief_markdown(session, today)` — the shorter daily brief (regime +
  portfolio + upcoming catalysts; no trade-process review). `build_report_markdown(
  session, period, today)` dispatches daily / weekly. Both reuse the existing
  section helpers + the forbidden-wording scan; no-account → an explicit
  placeholder.

### `scripts/generate_report.py`
- `--period daily|weekly` (default daily), `--date` (as-of), `--out` (default
  `$EXPORT_DIR` / `data/exports`), `--stdout`. Writes
  `report_<period>_<date>.md`. Read-only against the DB.

### `fsoctl.sh`
- New `report [period]` command (runs the generator in the api container with
  `./data` mounted so the export lands on the host).

### Docs
- `docs/OPERATIONS_RUNBOOK.md` "Reports" section + cron examples.

## Tests
- `tests/integration/test_report_generation.py`: daily omits the trade review,
  weekly includes it (both have regime/portfolio/catalysts, no forbidden
  wording); the script writes `report_daily_<date>.md`.
- `generate_report.py` added to the operations `--help` contract.

## Verification
- Offline: report-generation + operations pytest PASS; ruff clean; manual
  `--help`; `bash -n fsoctl.sh`.
- Docker (rebuilt api image): report-generation + operations pytest + ruff.

## Notes
- No app-route / schema change. Descriptive-only (wording-scanned). Next: 175
  Event-week briefing.
