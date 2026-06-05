# 175 — Event-Week Briefing (Phase 6)

**Status:** Done. A forward-looking catalyst briefing, reusing the Slice-174
report plumbing.

## Implemented

### `api/weekly_report.py`
- `build_event_week_briefing_markdown(session, today, horizon_days=7)` — lists the
  upcoming events within the window (sorted by date, then risk), each with its
  risk label / score and which current holdings it touches (the Slice-165
  held-ticker linkage), plus a holdings-exposure rollup. Preparation / exposure
  framing only; forbidden-wording scanned. `build_report_markdown` now dispatches
  `event-week` alongside `daily` / `weekly`.

### `scripts/generate_report.py` / `fsoctl.sh`
- `--period` gains `event-week`; `./fsoctl.sh report event-week` →
  `data/exports/report_event-week_<date>.md`.

### Docs
- `docs/OPERATIONS_RUNBOOK.md` "Reports" section updated.

## Tests (`tests/integration/test_report_generation.py`, +1)
- with an NVDA-linked earnings event 3 days out: the briefing lists it under the
  window + a Holdings-exposure section, no forbidden wording.

## Verification
- Offline: report-generation + operations pytest PASS; ruff clean; manual
  event-week smoke; `bash -n fsoctl.sh`.
- Docker (rebuilt api image): report-generation + operations pytest + ruff.

## Notes
- No app-route / schema change. Reuses the event-radar VM (incl. 165 held-ticker
  linkage) + the 174 report plumbing. Next: 176 Worker notification hook.
