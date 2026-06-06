# 207 — Per-Symbol Detail in Query Context (v3)

**Status:** Done. "NVDA 지표 보여줘" / "TSLA 어때" → the agent fetches that symbol's
stored indicators + price for the turn. Read-only, deterministic.

## Implemented (`finskillos/agent/context.py`)
- `build_query_context` extracts uppercase ticker candidates from the question
  (small acronym stoplist) and looks up each (≤3): `MarketRepository.latest_close`
  + `IndicatorRepository.latest_for` (1d) → "TICKER: close X, RSI Y, trend Z,
  momentum M (stored indicators, descriptive — not a signal)." Only tickers with
  **stored data** are included — that filter removes non-ticker words (RSI/FOMC).

## Boundary
Descriptive read-only; explicitly tagged "not a signal". No write path.

## Tests (`tests/test_agent_context.py` +1)
- seeded NVDA bar+indicator → "NVDA: … RSI …"; a non-ticker uppercase word → no
  symbol section.

## Verification
- Offline: context pytest PASS; ruff clean. Docker (rebuilt api): suites.
