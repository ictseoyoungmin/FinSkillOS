# 92 — Shared Live-Error Helper + Copy

Date: 2026-05-30

## Goal

The four Slice-80 live-error builders (risk_firewall / mission_control /
news_intelligence / trade_memory) each repeated the exception-detail rule and
two identical narrative sentences. The response objects are route-specific, but
the shared bits should live in one place so the state language
(`docs/v2_1/13_*`) cannot drift between tabs.

## Implemented

- New `api/live_state.py`:
  - `exc_detail(exc)` → `type(exc).__name__` (the Slice-80 "class name only,
    never the message/stack" rule, now defined once).
  - `LIVE_ERROR_DRIVER_NOTE` = "An error is surfaced instead of falling back to
    fixture data."
  - `LIVE_ERROR_WHY_IT_MATTERS` = "Errors are surfaced explicitly rather than
    masked with fixture data."
- All four routes now use `exc_detail(exc)` and the two shared constants. The
  route-specific phrasing (e.g. "Live risk evaluation failed", "Live news read
  failed") stays per route — only the genuinely shared sentences were
  centralised.

## Notes

- Pure dedup: the centralised strings are byte-identical to the previous inline
  copy, so the API responses are unchanged (the v4.2 contract + per-route tests
  confirm). A full shared *builder* is not feasible because each tab's response
  schema differs; this slice consolidates the shared helper + copy only.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest
  tests/test_api_{risk_firewall,mission_control,news_intelligence,trade_memory}.py
  tests/test_api_v42_contract.py tests/test_acceptance_safety_language.py -q`
  ✅ passed
- `docker compose run --rm api python -m pytest <four route tests + v42>` ✅ passed
- `docker compose run --rm --no-deps api python -m ruff check api/live_state.py
  api/routes/` ✅ All checks passed

## Known issues

- None. (`system_ops` POST handlers also use `type(exc).__name__`; adopting
  `exc_detail` there is an optional follow-up, left out to keep this slice
  scoped to the GET live-error builders.)
