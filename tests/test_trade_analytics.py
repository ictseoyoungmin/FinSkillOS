"""Trade analytics (by-ticker + by-day) — v4. Offline (sqlite)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import create_app
from finskillos.db.base import Base
from finskillos.db.repositories import AccountRepository
from finskillos.services.trade_analytics_service import (
    summarize_daily_trades,
    summarize_ticker_trades,
)
from finskillos.services.trade_journal_service import (
    TradeJournalInput,
    TradeJournalService,
)


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _seed(session):
    account = AccountRepository(session).create(name="Main", target_value=Decimal("1"))
    svc = TradeJournalService(session)
    rows = [
        ("NVDA", "BUY", date(2026, 6, 1), "10", "100", "1000"),
        ("NVDA", "BUY", date(2026, 6, 1), "5", "110", "550"),
        ("NVDA", "SELL", date(2026, 6, 5), "8", "130", "1040"),
        ("AAPL", "BUY", date(2026, 6, 5), "2", "200", "400"),
    ]
    for ticker, side, d, qty, price, amount in rows:
        svc.create_entry(
            TradeJournalInput(
                trade_date=d, ticker=ticker, side=side,
                quantity=Decimal(qty), price=Decimal(price), amount=Decimal(amount),
            )
        )
    session.commit()
    return account


def test_summarize_ticker_trades() -> None:
    session = _session()
    account = _seed(session)
    s = summarize_ticker_trades(session, account.id, "NVDA")
    assert s["trade_count"] == 3 and s["buy_count"] == 2 and s["sell_count"] == 1
    assert s["total_buy_amount"] == "1550.00" and s["total_sell_amount"] == "1040.00"
    assert s["net_cashflow"] == "-510.00"  # 1040 - 1550
    # weighted avg buy price: (100*10 + 110*5) / 15 = 103.3333
    assert s["avg_buy_price"].startswith("103.33")
    assert summarize_ticker_trades(session, account.id, "ZZZ")["trade_count"] == 0


def test_summarize_daily_trades() -> None:
    session = _session()
    account = _seed(session)
    rows = summarize_daily_trades(session, account.id, days=3650)
    by_date = {r["date"]: r for r in rows}
    assert by_date["2026-06-01"]["trade_count"] == 2  # two NVDA buys
    assert by_date["2026-06-05"]["sell_count"] == 1 and by_date["2026-06-05"]["buy_count"] == 1


def test_trade_analytics_tools_registered() -> None:
    names = {t["name"] for t in TestClient(create_app()).get("/api/agent/tools").json()["tools"]}
    assert {"read.trades_by_ticker", "read.trades_by_day"} <= names


def test_by_ticker_endpoint_no_db() -> None:
    # session=None offline → available=false with a clear note (never 500).
    body = TestClient(create_app()).get("/api/agent/trades/by-ticker?ticker=NVDA").json()
    assert body["available"] is False and body["ticker"] == "NVDA"


def test_ticker_summary_has_fifo_realized_and_winrate() -> None:
    session = _session()
    account = _seed(session)
    s = summarize_ticker_trades(session, account.id, "NVDA")
    # buy 10@100 + 5@110, sell 8@130 → FIFO realized (130-100)*8 = 240
    from decimal import Decimal
    assert Decimal(s["realized_pnl"]) == Decimal("240")
    assert s["closed_count"] == 1 and s["wins"] == 1 and s["win_rate"] == 1.0


def test_weekday_and_performance() -> None:
    from finskillos.services.trade_analytics_service import (
        summarize_by_weekday,
        summarize_ticker_performance,
    )

    session = _session()
    account = _seed(session)
    wk = {r["weekday"]: r for r in summarize_by_weekday(session, account.id)}
    assert len(wk) == 7
    perf = summarize_ticker_performance(session, account.id)
    nvda = next(r for r in perf if r["ticker"] == "NVDA")
    assert nvda["wins"] == 1 and nvda["win_rate"] == 1.0


def test_new_trade_tools_registered() -> None:
    names = {t["name"] for t in TestClient(create_app()).get("/api/agent/tools").json()["tools"]}
    assert {"read.trades_by_weekday", "read.trade_performance"} <= names
