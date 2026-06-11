"""Trade analytics — per-ticker + daily aggregates over the journal — v4.

Descriptive summaries over the stored trades (now populated from real Toss
executed-order history). Amounts are KRW (the sync converts USD trades). Read-only.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from finskillos.db.repositories import TradeRepository

__all__ = [
    "summarize_ticker_trades",
    "summarize_daily_trades",
    "summarize_by_weekday",
    "summarize_ticker_performance",
]

_BUY = {"BUY", "LONG"}
_SELL = {"SELL", "SHORT"}
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _fifo_realized(trades) -> dict:
    """FIFO-match SELLs against prior BUYs → realized P&L + win/loss per close.

    Long-only model (BUY opens, SELL closes); a SELL with no matching BUY is
    skipped (no cost basis). Returns realized events for further grouping.
    Amounts/prices are KRW. The same-day order follows trade_date then insertion.
    """

    lots: deque[list] = deque()  # [remaining_qty, buy_price]
    events: list[tuple] = []  # (close_date, realized) per closing SELL
    for trade in trades:
        qty = trade.quantity or Decimal("0")
        price = trade.price or Decimal("0")
        if trade.side in _BUY:
            if qty > 0:
                lots.append([qty, price])
        elif trade.side in _SELL:
            remaining = qty
            realized = Decimal("0")
            matched_any = False
            while remaining > 0 and lots:
                lot = lots[0]
                matched = min(remaining, lot[0])
                realized += (price - lot[1]) * matched
                lot[0] -= matched
                remaining -= matched
                matched_any = True
                if lot[0] <= 0:
                    lots.popleft()
            if matched_any:
                events.append((trade.trade_date, realized))
    wins = sum(1 for _, r in events if r > 0)
    losses = sum(1 for _, r in events if r < 0)
    decided = wins + losses
    return {
        "realized_pnl": sum((r for _, r in events), Decimal("0")),
        "closed_count": len(events),
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / decided) if decided else None,
        "events": events,
    }


def _sum(values) -> Decimal:
    return sum((v or Decimal("0") for v in values), Decimal("0"))


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
    buy_amt, sell_amt = _sum(t.amount for t in buys), _sum(t.amount for t in sells)
    fifo = _fifo_realized(trades)
    win_rate = fifo["win_rate"]
    return {
        "ticker": symbol,
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
        for close_date, realized in _fifo_realized(
            repo.list_by_ticker(account_id, ticker)
        )["events"]:
            if start <= close_date <= end:
                b = buckets[close_date.weekday()]
                b["realized"] += realized
                if realized > 0:
                    b["wins"] += 1
                elif realized < 0:
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
        fifo = _fifo_realized(repo.list_by_ticker(account_id, ticker))
        if fifo["closed_count"] == 0:
            continue
        wr = fifo["win_rate"]
        rows.append({
            "ticker": ticker,
            "realized_pnl": str(fifo["realized_pnl"]),
            "closed_count": fifo["closed_count"],
            "wins": fifo["wins"],
            "losses": fifo["losses"],
            "win_rate": round(wr, 4) if wr is not None else None,
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
