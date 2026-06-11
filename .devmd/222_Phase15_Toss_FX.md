# 222 — v4 Phase 15: Toss Exchange Rate as FX Source

**Status:** Done. `usd_krw_rate()` now prefers the Toss exchange rate when Toss is
configured, falling back to Yahoo, then the cached/default rate.

- `toss/client.py` — `exchange_rate(base, quote)` sends the required
  `baseCurrency`/`quoteCurrency` params → `{rate, midRate, …}`.
- `agent/fx.py` — default fetcher is `_default_usd_krw` (Toss → Yahoo); env
  `FINSKILLOS_USD_KRW_RATE` still forces a fixed rate; never raises.
- tests: client currency params; default prefers Toss then Yahoo; Toss None when
  unconfigured.
