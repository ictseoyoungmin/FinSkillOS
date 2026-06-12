# 244 — v4: Native price + currency (per-currency exact realized P&L)

## Status
COMPLETE — Docker-verified, committed on `main`.

Closes the last trade-analytics caveat: absolute realized P&L was *approximate*
for older USD trades because the sync stored `price` already KRW-converted at the
sync-time FX rate. Now `price` is the trade's **native** currency and a `currency`
marker is stored alongside, so realized P&L is summed **exactly per currency**
(USD trades in USD, KR trades in KRW — never mixed). Ratios (win rate, profit
factor, MFE/MAE) were already currency-invariant; this makes the absolute amounts
exact too.

## Implemented
- **Migration `0019_trade_currency`** — additive nullable `trades.currency`
  (`String(8)`, no server default; legacy rows stay NULL and analytics infer the
  currency from the ticker until a re-sync backfills it). Single alembic head.
- **Model / repo / journal** — `Trade.currency`; `TradeRepository.create(currency=)`;
  `TradeJournalInput.currency` threaded through `create_entry`.
- **Sync (`brokerage_sync_service.sync_toss_trades`)** — stores `price` **native**
  (new `_dec`, no FX) + `currency`; `amount`/`fees` stay KRW for the cashflow
  views. New `replace=True` deletes existing Toss rows and re-imports them in the
  **same transaction** (atomic — a failure rolls back with no loss) to backfill
  native price + currency onto legacy rows. Returns `removed`.
- **Analytics (`trade_analytics_service`)**
  - `_ticker_currency(trades)` — stored currency, else KR-6-digit→KRW / else USD.
  - `summarize_ticker_trades` — adds `currency`; buy/sell amounts now native
    (`price×qty`) so they share the realized P&L's currency.
  - `summarize_overall_stats` — adds `by_currency` (exact per-currency realized /
    PF / expectancy / avg win-loss / best-worst); top-level realized kept but is
    only exact for a single-currency account (documented; prefer `by_currency`).
  - `summarize_ticker_performance` — adds `currency` per row.
  - `summarize_ticker_excursion` — drops FX scaling (native entry matches native
    candles → MFE/MAE invariant); `fx_rate` kept as an optional override (default 1).
- **API** — `currency` on ticker/performance responses; `TradeCurrencyStatsVM` +
  `byCurrency` on the stats response. `POST /agent/sync/trades/apply?replace=true`
  for the one-time backfill (atomic; reports replaced count).
- **Frontend** — `formatMoney(value, currency)` (USD/KRW-aware, KRW fallback);
  `TradeAnalyticsPanel` renders per-currency realized blocks
  (`trade-analytics-cur-{CUR}`), per-ticker realized in native currency, and drops
  the mixed-currency realized column from the weekday table (keeps win rate +
  counts). `TradeStats.byCurrency` / `TradeCurrencyStats` / `TradePerformanceRow.currency`.

## Tests
- `tests/test_toss_trade_sync.py` — native price kept (USD `185`, not ×1350),
  `currency` recorded, `amount` stays KRW; `replace=True` re-imports atomically
  (`removed==2`, no duplication).
- `tests/test_trade_analytics.py` — ticker summary exposes `currency`;
  `summarize_overall_stats` `by_currency` separates USD (+30) / KRW (+1000).
- Existing 15 analytics tests + excursion tests unchanged-green (rate-1 path).

## Verification
- `FINSKILLOS_SKIP_DOTENV=1 pytest tests/ --ignore=tests/integration` — green
  (the one pre-existing `test_event_radar_can_return_live_db_read_model` date-window
  failure reproduces on clean `main` and is unrelated).
- `docker compose build api worker web`; in-container
  `pytest test_trade_analytics + test_toss_trade_sync + test_api_agent_sync +
  test_migration_safety` — green; `web npm run build` — green.
- Live: `alembic upgrade head` (api) → `POST /agent/sync/trades/apply?replace=true`
  to backfill, then `up -d` recreate.

## Notes / known issues
- Top-level `realized_pnl` / `expectancy` / `profit_factor` on the stats response
  still sum across currencies (kept for backward-compat); exact only when the
  account is single-currency — the UI reads `byCurrency`.
- Weekday realized was mixed-currency and is intentionally dropped from the table;
  weekday win rate (the real insight) is currency-invariant and retained.
- Descriptive-only: no buy/sell/execution wording anywhere.
