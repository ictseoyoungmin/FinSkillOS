# 99 — Trade Memory Entry Edit / Delete / CSV Export (API)

Date: 2026-05-31

## Goal

First half of the "Trade Memory edit/delete + export" queue item: the backend
seam. The journal could only be appended to (POST). Add update, delete, and a
CSV export of the recent entries, mirroring the existing POST contract
(structured JSON result, forbidden-wording guard, never a raw stack). Frontend
UI is the follow-up slice.

## Implemented

- `finskillos/db/repositories/trade_repo.py`: `TradeRepository.delete(trade_id)`
  (raises `LookupError` if absent), alongside the existing `create` / `update`.
- `finskillos/services/trade_journal_service.py`:
  `TradeJournalService.delete_entry(trade_id)`.
- `api/routes/trade_memory.py`:
  - `PUT /api/trade-memory/entries/{entry_id}` — update one entry via
    `update_entry`. Same validation as POST (valid id, ISO date, forbidden
    wording) plus an `invalid_entry_id` reject for a non-UUID path.
  - `DELETE /api/trade-memory/entries/{entry_id}` — delete one entry; a missing
    row maps to a `validation_error` reject (LookupError), never a 500.
  - `GET /api/trade-memory/export.csv` — recent entries as a deterministic,
    descriptive CSV (`text/csv`, attachment). Works in every mode (forced
    fixture / db-unavailable / live) by reusing the snapshot resolver.
  - Refactor: shared `_resolve_payload(use_fixture)` (read + export both use
    it), `_journal_input(payload, trade_date)` (POST + PUT share the
    `TradeJournalInput` build), and `_entry_write_result(session, op, ...)` (the
    OK / REJECTED / ERROR mapping the POST already used, now shared by all three
    mutating handlers). The giant duplicated try/except and result builders are
    gone.

## Tests added (`tests/test_api_trade_memory.py`)

- `test_put_trade_entry_updates_live_db` — PUT updates ticker + notes; the next
  GET reflects them.
- `test_put_trade_entry_rejects_invalid_entry_id` / `_rejects_forbidden_wording`.
- `test_delete_trade_entry_removes_live_db` — DELETE removes the row; GET shows
  zero entries / `tradeCount == 0`.
- `test_delete_trade_entry_missing_row_rejected` — unknown id → REJECTED
  `validation_error`.
- `test_export_trade_memory_csv_fixture` / `_live` — CSV headers + content type +
  attachment disposition; live export contains the ticker and carries no
  forbidden wording (descriptive-only).

## Notes

- Descriptive-only: the CSV exports stored journal fields verbatim and the
  forbidden-wording guard already gates every write, so no execution wording is
  introduced. The live export test asserts the `_FORBIDDEN_WORDS` are absent.
- No unique-constraint / migration changes; delete is a plain row removal.

## Verification

- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_trade_memory.py -q`
  ✅ 24 passed
- `FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q` ✅ all passed
- `python3 -m ruff check api/routes/trade_memory.py
  finskillos/db/repositories/trade_repo.py
  finskillos/services/trade_journal_service.py tests/test_api_trade_memory.py`
  ✅ All checks passed
- `docker compose run --rm api python -m pytest tests/test_api_trade_memory.py
  tests/test_api_v42_contract.py -q` ✅ 30 passed
- `docker compose run --rm --no-deps api ruff check <changed files>` ✅ clean

## Known issues

- Frontend edit/delete UI + export button is the follow-up slice (100).
