"""Trade analytics — per-ticker + daily aggregates over the journal — v4.

Descriptive summaries over the stored trades (now populated from real Toss
executed-order history). ``price`` is the trade's **native** currency (USD for US
tickers, KRW for KR), so per-ticker realized P&L is exact in that currency and the
account-wide stats break realized down per currency. The KRW ``amount`` column
still feeds the cross-ticker cashflow (daily) views. Read-only.
"""

from __future__ import annotations

from collections import defaultdict, deque, namedtuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from finskillos.db.repositories import TradeRepository

__all__ = [
    "summarize_ticker_trades",
    "summarize_daily_trades",
    "summarize_by_weekday",
    "summarize_ticker_performance",
    "summarize_ticker_excursion",
    "summarize_overall_stats",
    "realized_pnl_timeseries",
]

# One closed lot: a portion of a position opened then closed (FIFO).
CloseEvent = namedtuple(
    "CloseEvent",
    "close_date realized holding_days entry_date entry_price direction qty",
)

_BUY = {"BUY", "LONG"}
_SELL = {"SELL", "SHORT"}
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _sign(x) -> int:
    return (x > 0) - (x < 0)


def _ticker_currency(trades) -> str:
    """Native currency of a (single-ticker) trade list.

    Uses the stored ``currency`` once a Toss re-sync has backfilled it; legacy
    rows fall back to a shape heuristic (KR 6-digit numeric → KRW, else USD)."""

    for trade in trades:
        cur = getattr(trade, "currency", None)
        if cur:
            return str(cur).upper()
    sym = (trades[0].ticker or "").strip().upper() if trades else ""
    return "KRW" if (sym.isdigit() and len(sym) == 6) else "USD"


def _streaks(realized_seq) -> dict:
    """Max win/loss streak + current signed streak over ordered closes."""

    max_win = max_loss = run = run_sign = 0
    for realized in realized_seq:
        s = _sign(realized)
        if s == 0:
            continue
        run = run + 1 if s == run_sign else 1
        run_sign = s
        if s > 0:
            max_win = max(max_win, run)
        else:
            max_loss = max(max_loss, run)
    return {
        "max_win_streak": max_win,
        "max_loss_streak": max_loss,
        "current_streak": run_sign * run,  # + winning, − losing
    }


def _fifo_realized(trades) -> dict:
    """Signed-FIFO realized P&L — handles **long and short** positions.

    Each trade is a signed delta (BUY +qty, SELL −qty). A delta opposite to the
    front lot closes it FIFO (long lot closed by a sell, short lot closed by a
    buy); a same-direction delta opens/extends a lot. Realized per close, holding
    days (entry→exit), win/loss, and streaks. Prices/realized are in the trade's
    native currency (a single ticker is one currency).
    """

    lots: deque[list] = deque()  # [signed_qty, price, entry_date]
    events: list[CloseEvent] = []
    for trade in trades:
        qty = trade.quantity or Decimal("0")
        if qty <= 0:
            continue
        price = trade.price or Decimal("0")
        delta = qty if trade.side in _BUY else -qty
        while delta != 0 and lots and _sign(delta) != _sign(lots[0][0]):
            lot = lots[0]
            matched = min(abs(delta), abs(lot[0]))
            long_lot = lot[0] > 0
            realized = (
                (price - lot[1]) * matched if long_lot else (lot[1] - price) * matched
            )
            events.append(
                CloseEvent(
                    close_date=trade.trade_date,
                    realized=realized,
                    holding_days=(trade.trade_date - lot[2]).days,
                    entry_date=lot[2],
                    entry_price=lot[1],
                    direction="long" if long_lot else "short",
                    qty=matched,
                )
            )
            lot[0] -= _sign(lot[0]) * matched
            delta -= _sign(delta) * matched
            if lot[0] == 0:
                lots.popleft()
        if delta != 0:
            lots.append([delta, price, trade.trade_date])

    wins = sum(1 for e in events if e.realized > 0)
    losses = sum(1 for e in events if e.realized < 0)
    decided = wins + losses
    holds = [e.holding_days for e in events]
    result = {
        "realized_pnl": sum((e.realized for e in events), Decimal("0")),
        "closed_count": len(events),
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / decided) if decided else None,
        "avg_holding_days": round(sum(holds) / len(holds), 1) if holds else None,
        "events": events,
    }
    result.update(_streaks([e.realized for e in events]))
    return result


def _close_stats(events) -> dict:
    """Expectancy / profit factor / avg win-loss / win-vs-loss holding from closes.

    Absolute amounts are in the closes' native currency (exact within one ticker /
    one currency); ratios (profit factor, win rate) and holding days are
    currency-invariant. Mixing currencies in one call makes the amounts indicative
    only — callers split by currency where that matters."""

    realized = [e.realized for e in events]
    wins = [r for r in realized if r > 0]
    losses = [r for r in realized if r < 0]
    gross_profit = sum(wins, Decimal("0"))
    gross_loss = -sum(losses, Decimal("0"))
    win_holds = [e.holding_days for e in events if e.realized > 0]
    loss_holds = [e.holding_days for e in events if e.realized < 0]

    def _avg(values):
        return round(sum(values) / len(values), 1) if values else None

    return {
        "profit_factor": str(round(gross_profit / gross_loss, 3))
        if gross_loss > 0
        else None,
        "expectancy": str(round(sum(realized, Decimal("0")) / len(realized), 2))
        if realized
        else None,
        "avg_win": str(round(gross_profit / len(wins), 2)) if wins else None,
        "avg_loss": str(round(-gross_loss / len(losses), 2)) if losses else None,
        "avg_win_holding_days": _avg(win_holds),
        "avg_loss_holding_days": _avg(loss_holds),
        "best_trade": str(max(realized)) if realized else None,
        "worst_trade": str(min(realized)) if realized else None,
    }


def _currency_stats(events) -> dict:
    """Realized totals + close stats for a single-currency event list."""

    wins = sum(1 for e in events if e.realized > 0)
    losses = sum(1 for e in events if e.realized < 0)
    decided = wins + losses
    return {
        "closed_count": len(events),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / decided, 4) if decided else None,
        "realized_pnl": str(sum((e.realized for e in events), Decimal("0"))),
        **_close_stats(events),
    }


def summarize_overall_stats(session, account_id) -> dict:
    """Account-wide closed-trade stats: win rate, expectancy, profit factor, etc.

    Positions are FIFO-matched per ticker, then closes are aggregated. Currency-
    invariant fields (counts, win rate, holding days, streaks) span all trades;
    realized P&L / expectancy / profit factor are also broken out per native
    currency in ``by_currency`` so USD and KRW amounts are never mixed. The
    top-level realized figures sum across currencies and are only exact when the
    account is single-currency — prefer ``by_currency`` for amounts."""

    repo = TradeRepository(session)
    tickers = {t.ticker for t in repo.list_for_account(account_id)}
    events: list = []
    by_cur: dict[str, list] = defaultdict(list)
    for ticker in tickers:
        trades = repo.list_by_ticker(account_id, ticker)
        evs = _fifo_realized(trades)["events"]
        events.extend(evs)
        if evs:
            by_cur[_ticker_currency(trades)].extend(evs)
    if not events:
        return {"closed_count": 0}
    wins = sum(1 for e in events if e.realized > 0)
    losses = sum(1 for e in events if e.realized < 0)
    decided = wins + losses
    holds = [e.holding_days for e in events]
    stats = {
        "closed_count": len(events),
        "tickers": len(tickers),
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / decided, 4) if decided else None,
        "realized_pnl": str(sum((e.realized for e in events), Decimal("0"))),
        "avg_holding_days": round(sum(holds) / len(holds), 1) if holds else None,
        "by_currency": {cur: _currency_stats(evs) for cur, evs in by_cur.items()},
    }
    stats.update(_close_stats(events))
    return stats


def realized_pnl_timeseries(session, account_id, *, fx_rate=None) -> list[dict]:
    """Cumulative realized P&L by close date — a single KRW-equivalent curve.

    Each FIFO close is attributed to its close date; USD closes are converted at
    ``fx_rate`` (default current USD/KRW), KR closes at 1, then summed cumulatively.
    Returns ``[{"date": iso, "value": str}]`` ascending. Descriptive performance
    trend (KRW-equiv at one rate — a trend aid, not exact per-day FX)."""

    repo = TradeRepository(session)
    tickers = {t.ticker for t in repo.list_for_account(account_id)}
    if fx_rate is None:
        from finskillos.agent.fx import usd_krw_rate

        fx_rate = usd_krw_rate()
    rate = Decimal(str(fx_rate))
    daily: dict = defaultdict(lambda: Decimal("0"))
    for ticker in tickers:
        trades = repo.list_by_ticker(account_id, ticker)
        mult = rate if _ticker_currency(trades) == "USD" else Decimal("1")
        for event in _fifo_realized(trades)["events"]:
            daily[event.close_date] += event.realized * mult
    rows: list[dict] = []
    cumulative = Decimal("0")
    for day in sorted(daily):
        cumulative += daily[day]
        rows.append(
            {"date": day.isoformat(), "value": str(cumulative.quantize(Decimal("0.01")))}
        )
    return rows


def _sum(values) -> Decimal:
    return sum((v or Decimal("0") for v in values), Decimal("0"))


def _notional(trades) -> Decimal:
    """Native trade value (Σ price×qty) — a single ticker is one currency."""

    return _sum(
        (t.price or Decimal("0")) * (t.quantity or Decimal("0")) for t in trades
    ).quantize(Decimal("0.01"))


def _wavg_price(trades) -> Decimal | None:
    qty = _sum(t.quantity for t in trades)
    if qty == 0:
        return None
    notional = _sum((t.price or Decimal("0")) * (t.quantity or Decimal("0")) for t in trades)
    return (notional / qty).quantize(Decimal("0.0001"))


def summarize_ticker_trades(session, account_id, ticker: str) -> dict:
    """Per-ticker trade summary: counts, amounts, net cashflow, avg prices, dates."""

    trades = TradeRepository(session).list_by_ticker(account_id, ticker)
    symbol = (ticker or "").strip().upper()
    if not trades:
        return {"ticker": symbol, "trade_count": 0}
    buys = [t for t in trades if t.side in _BUY]
    sells = [t for t in trades if t.side in _SELL]
    # Native (price×qty) so amounts share the realized P&L's currency.
    buy_amt, sell_amt = _notional(buys), _notional(sells)
    fifo = _fifo_realized(trades)
    win_rate = fifo["win_rate"]
    stats = _close_stats(fifo["events"])
    return {
        **stats,
        "ticker": symbol,
        "currency": _ticker_currency(trades),
        "trade_count": len(trades),
        "buy_count": len(buys),
        "sell_count": len(sells),
        "total_buy_amount": str(buy_amt),
        "total_sell_amount": str(sell_amt),
        "net_cashflow": str(sell_amt - buy_amt),
        "total_fees": str(_sum(t.fees for t in trades)),
        "avg_buy_price": str(_wavg_price(buys)) if buys else None,
        "avg_sell_price": str(_wavg_price(sells)) if sells else None,
        "realized_pnl": str(fifo["realized_pnl"]),
        "closed_count": fifo["closed_count"],
        "wins": fifo["wins"],
        "losses": fifo["losses"],
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "avg_holding_days": fifo["avg_holding_days"],
        "max_win_streak": fifo["max_win_streak"],
        "max_loss_streak": fifo["max_loss_streak"],
        "current_streak": fifo["current_streak"],
        "first_date": trades[0].trade_date.isoformat(),
        "last_date": trades[-1].trade_date.isoformat(),
    }


def summarize_by_weekday(session, account_id, *, days: int = 3650) -> list[dict]:
    """Trade activity + FIFO realized P&L grouped by weekday (Mon–Sun).

    Realized P&L attributes each closing SELL to its weekday (per-ticker FIFO)."""

    end = datetime.now(tz=timezone.utc).date()
    start = end - timedelta(days=max(1, days))
    repo = TradeRepository(session)
    trades = repo.list_by_date_range(account_id, start=start, end=end)
    buckets = {
        i: {"count": 0, "buy": 0, "sell": 0, "realized": Decimal("0"),
            "wins": 0, "losses": 0}
        for i in range(7)
    }
    for trade in trades:
        b = buckets[trade.trade_date.weekday()]
        b["count"] += 1
        if trade.side in _BUY:
            b["buy"] += 1
        elif trade.side in _SELL:
            b["sell"] += 1
    # realized per close → attribute to the close's weekday (per-ticker FIFO).
    for ticker in {t.ticker for t in trades}:
        for ev in _fifo_realized(repo.list_by_ticker(account_id, ticker))["events"]:
            if start <= ev.close_date <= end:
                b = buckets[ev.close_date.weekday()]
                b["realized"] += ev.realized
                if ev.realized > 0:
                    b["wins"] += 1
                elif ev.realized < 0:
                    b["losses"] += 1
    rows = []
    for i in range(7):
        b = buckets[i]
        decided = b["wins"] + b["losses"]
        rows.append({
            "weekday": _WEEKDAYS[i],
            "trade_count": b["count"],
            "buy_count": b["buy"],
            "sell_count": b["sell"],
            "realized_pnl": str(b["realized"]),
            "win_rate": round(b["wins"] / decided, 4) if decided else None,
        })
    return rows


def summarize_ticker_performance(session, account_id, *, top: int = 25) -> list[dict]:
    """Per-ticker realized P&L + win rate, ranked by realized P&L (FIFO)."""

    repo = TradeRepository(session)
    tickers = {t.ticker for t in repo.list_for_account(account_id)}
    rows = []
    for ticker in tickers:
        trades = repo.list_by_ticker(account_id, ticker)
        fifo = _fifo_realized(trades)
        if fifo["closed_count"] == 0:
            continue
        wr = fifo["win_rate"]
        rows.append({
            "ticker": ticker,
            "currency": _ticker_currency(trades),
            "realized_pnl": str(fifo["realized_pnl"]),
            "closed_count": fifo["closed_count"],
            "wins": fifo["wins"],
            "losses": fifo["losses"],
            "win_rate": round(wr, 4) if wr is not None else None,
            "avg_holding_days": fifo["avg_holding_days"],
        })
    rows.sort(key=lambda r: Decimal(r["realized_pnl"]), reverse=True)
    return rows[: max(1, top)]


def summarize_daily_trades(session, account_id, *, days: int = 30) -> list[dict]:
    """Trades grouped by day over the last ``days`` — count, sides, amounts, net."""

    end = datetime.now(tz=timezone.utc).date()
    start = end - timedelta(days=max(1, days))
    trades = TradeRepository(session).list_by_date_range(
        account_id, start=start, end=end
    )
    buckets: dict = {}
    for trade in trades:
        bucket = buckets.setdefault(
            trade.trade_date,
            {"count": 0, "buy": 0, "sell": 0,
             "buy_amt": Decimal("0"), "sell_amt": Decimal("0")},
        )
        bucket["count"] += 1
        if trade.side in _BUY:
            bucket["buy"] += 1
            bucket["buy_amt"] += trade.amount or Decimal("0")
        elif trade.side in _SELL:
            bucket["sell"] += 1
            bucket["sell_amt"] += trade.amount or Decimal("0")
    return [
        {
            "date": day.isoformat(),
            "trade_count": v["count"],
            "buy_count": v["buy"],
            "sell_count": v["sell"],
            "buy_amount": str(v["buy_amt"]),
            "sell_amount": str(v["sell_amt"]),
            "net": str(v["sell_amt"] - v["buy_amt"]),
        }
        for day, v in sorted(buckets.items(), reverse=True)
    ]


def summarize_ticker_excursion(
    session, account_id, ticker: str, *, bar_fetcher=None, fx_rate=None
) -> dict:
    """MFE/MAE per ticker — max favorable / adverse excursion during each closed
    lot's holding window, from daily candles.

    For each closed lot, finds candles in [entry_date, close_date] and measures how
    far price moved in favour / against, as a fraction of entry price:
      long  → MFE=(maxHigh−entry)/entry, MAE=(minLow−entry)/entry
      short → MFE=(entry−minLow)/entry,  MAE=(entry−maxHigh)/entry

    Entry prices are stored in the trade's native currency, which already matches
    the candle currency (USD candles for US tickers, KRW for KR), so no FX scaling
    is needed and the MFE/MAE ratios are currency-invariant. ``fx_rate`` is kept as
    an optional override (default 1). ``bar_fetcher(ticker, start)`` is injectable
    (default Toss candles); held tickers often lack stored bars, so this fetches
    fresh. Read-only.
    """

    trades = TradeRepository(session).list_by_ticker(account_id, ticker)
    events = _fifo_realized(trades)["events"]
    symbol = (ticker or "").strip().upper()
    if not events:
        return {"ticker": symbol, "lots": 0}

    if bar_fetcher is None:
        from finskillos.brokerage.toss.market import TossMarketDataAdapter

        def bar_fetcher(sym, start):
            return TossMarketDataAdapter().fetch_bars(sym, timeframe="1d", start=start)

    # Native entry price matches native candles → no FX scaling (rate 1 by
    # default; ``fx_rate`` is an explicit override for tests / mismatched feeds).
    rate = Decimal(str(fx_rate)) if fx_rate is not None else Decimal("1")

    start = min(e.entry_date for e in events)
    try:
        bars = bar_fetcher(symbol, start)
    except Exception:  # noqa: BLE001 - excursion is best-effort
        bars = []
    by_date: dict = {}
    for bar in bars or []:
        bt = bar.bar_time
        day = bt.date() if hasattr(bt, "date") else bt
        if bar.high is not None and bar.low is not None:
            by_date[day] = (bar.high * rate, bar.low * rate)

    mfes: list[Decimal] = []
    maes: list[Decimal] = []
    for e in events:
        entry = e.entry_price
        if entry == 0:
            continue
        window = [
            hl for day, hl in by_date.items() if e.entry_date <= day <= e.close_date
        ]
        if not window:
            continue
        hi = max(h for h, _ in window)
        lo = min(low for _, low in window)
        if e.direction == "long":
            mfes.append((hi - entry) / entry)
            maes.append((lo - entry) / entry)
        else:  # short
            mfes.append((entry - lo) / entry)
            maes.append((entry - hi) / entry)

    n = len(mfes)
    return {
        "ticker": symbol,
        "lots": len(events),
        "lots_with_bars": n,
        "avg_mfe": str(round(sum(mfes) / n, 4)) if n else None,
        "avg_mae": str(round(sum(maes) / n, 4)) if n else None,
        "best_mfe": str(round(max(mfes), 4)) if n else None,
        "worst_mae": str(round(min(maes), 4)) if n else None,
    }
