"""Trade analytics — per-ticker + daily aggregates over the journal — v4.

Descriptive summaries over the stored trades (now populated from real Toss
executed-order history). Amounts are KRW (the sync converts USD trades). Read-only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from finskillos.db.repositories import TradeRepository

__all__ = ["summarize_ticker_trades", "summarize_daily_trades"]

_BUY = {"BUY", "LONG"}
_SELL = {"SELL", "SHORT"}


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
        "first_date": trades[0].trade_date.isoformat(),
        "last_date": trades[-1].trade_date.isoformat(),
    }


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
