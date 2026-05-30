# 91 — Shared api/timeutil (dedup _as_utc / _iso)

Date: 2026-05-30

## Goal

Six API route modules carried byte-identical `_as_utc` (4 routes) and
near-identical `_iso` (4 routes, 3 minor variants) timestamp helpers. Define the
timestamp contract once.

## Implemented

- New `api/timeutil.py`:
  - `to_utc(value)` — UTC-aware datetime (naive assumed UTC). Identical to the
    four duplicated `_as_utc` bodies.
  - `iso(value)` — ISO-8601 string normalised to UTC; non-datetime values fall
    back to `str(value)` (for `date` this equals `date.isoformat()`).
- `market_kernel`, `symbol_lab`, `analysis_workspace`, `system_ops` import
  `to_utc as _as_utc`; `control_room`, `trade_memory`, `market_kernel`,
  `symbol_lab` import `iso as _iso`. Local helper defs removed; call sites
  unchanged via the import aliases.

## Notes

- The three prior `_iso` variants differed only for aware non-UTC datetimes and
  `date`/non-datetime inputs. Real inputs are UTC/naive datetimes and `date`s,
  for which the consolidated `iso` produces identical output — confirmed by the
  full timestamp-heavy route test suites. `iso` now always normalises aware
  datetimes to UTC (the most correct of the three variants).
- No behavioural / API change.

## Tests added

- `tests/test_timeutil.py` — `to_utc` naive/aware, `iso` naive/aware/date/None.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_timeutil.py
  tests/test_api_{control_room,market_kernel,symbol_lab,trade_memory,analysis_workspace,system_ops}.py -q`
  ✅ passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `docker compose run --rm api python -m pytest <route tests + timeutil + v42>`
  ✅ passed
- `docker compose run --rm --no-deps api python -m ruff check api/timeutil.py
  api/routes/ tests/test_timeutil.py` ✅ All checks passed

## Known issues

- None.
