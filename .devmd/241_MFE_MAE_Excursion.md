# 241 — v4: MFE/MAE Excursion (via Toss candles)

Max favorable / adverse excursion per ticker — how far price moved in favour /
against during each closed lot's holding window.

- `CloseEvent` namedtuple — FIFO events now carry entry_date/price/direction/qty.
- `summarize_ticker_excursion(session, account_id, ticker)` — per closed lot, finds
  daily candles in [entry, exit] → long: MFE=(maxHigh−entry)/entry,
  MAE=(minLow−entry)/entry; short flips. **Fetches fresh Toss candles** (held
  tickers lack stored bars). **FX**: entry is KRW (sync-converted), so US-ticker
  candles (USD) are scaled ×usd_krw_rate (KR 6-digit untouched) — the ratio is
  consistent. `GET /agent/trades/excursion?ticker=` (`read.trade_excursion`).
- tests: MFE/MAE (injected candles), KR no-scaling, no-candles, tool registered.

## Bug caught + fixed (live)
First live run gave MFE −0.96 (nonsense): entry KRW vs US candle USD. Fixed by
USD→KRW scaling. After fix — NVDL: 48 lots, avg MFE +16.8% / avg MAE −14.0% / best
+47% / worst −55%.

## Caveats
Long+short; needs Toss candle coverage (lots_with_bars=0 otherwise). US FX uses the
current rate (≈ sync-time), so old trades are approximate. Descriptive aid.
