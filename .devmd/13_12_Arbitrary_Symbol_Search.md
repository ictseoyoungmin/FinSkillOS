# 13.12 Arbitrary Symbol Search

Status: DONE_AS_ARBITRARY_SYMBOL_SEARCH_V0
Date: 2026-05-24

## Goal

Allow Symbol Lab users to search any ticker text, while preserving the existing stored-evidence model.

The ten visible tickers are now shortcuts, not the full supported universe. If a searched symbol has no stored snapshot, the UI returns a structured `MISSING` state instead of implying the symbol is unsupported.

## Scope

- Symbol Lab accepts arbitrary ticker input and normalizes it to uppercase.
- Stored fixture symbols remain available as quick shortcut buttons.
- Unknown symbols return deterministic missing-state cards, setup hints, and empty tables.
- No live market-data adapter is introduced in this slice.
- No trade execution, brokerage integration, or deployment operations are included.

## Implementation

- `api/schemas/symbol_lab.py` exposes `symbolUniverse`.
- `api/fixtures/symbol_lab.py` separates shortcut universe metadata from arbitrary search handling.
- `frontend/src/features/market/components/TickerSearch.tsx` supports free-text input plus shortcut suggestions.
- `frontend/src/pages/symbol-lab/SymbolLabPage.tsx` passes backend-provided shortcut metadata into the search panel.
- API and E2E tests cover stored shortcuts and arbitrary ticker search.

## Verification

- `timeout 90 python3 -m pytest tests/test_api_symbol_lab.py -q`
- `python3 -m compileall api`
- `python3 -m ruff check api tests`
- `docker compose -f docker-compose.yml build api web e2e`
- `docker compose -f docker-compose.yml up -d api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npm run test:e2e`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npm run test:visual:update`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npm run test:visual`

## Follow-Up

Live quote or indicator population for arbitrary symbols should be handled by a separate market-data ingestion/read-through slice.
