# 210 — FX Rate + USD→KRW Ingestion Conversion (v3)

**Status:** Done. Fixes the currency mismatch — a USD brokerage paste ($ values)
was stored as raw KRW numbers (~1000× too small), breaking the total / limits /
progress. Now USD holdings convert to KRW on import.

## Implemented

### `finskillos/agent/fx.py`
- `usd_krw_rate(fetcher=None)` → KRW per USD. `FINSKILLOS_USD_KRW_RATE` env forces
  a fixed rate (tests / control); otherwise a live Yahoo `KRW=X` fetch cached 1h,
  fetcher injectable; any failure falls back to the last cached value or
  `DEFAULT_USD_KRW` (1350). Never raises. (A future Toss source registers as a
  `fetcher`.)

### Conversion (`finskillos/agent/ingest.py`)
- `parse_portfolio_paste(text, *, usd_krw_rate)` converts a line's market value /
  average cost when it has `$`. `proposal_from_records(records, *, usd_krw_rate)`
  converts when a record's `currency == "USD"`. KRW (₩) untouched.

### Chat (`finskillos/agent/chat.py`)
- `run_chat` resolves the rate only when the paste has `$`, passes it to both the
  deterministic parser and the LLM extraction.
- System prompt: extract EVERY row, map company names (KO/EN) to US tickers, use
  the market-value column, keep the ORIGINAL number + a `"currency"` field.

## Tests (`tests/test_agent_fx.py`, +6)
- env override; injected fetcher; fetch-failure fallback; parse converts USD lines
  / keeps KRW; records convert on USD flag; chat USD paste → KRW in the CSV.

## Verification
- Offline: fx + ingest + chat pytest PASS; ruff clean. Docker (rebuilt api): suites.

## Notes
- Default is live FX (env blank). Next (211): auto-reconcile the snapshot baseline
  after an agent import + double-apply guard + extraction completeness.
