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


def test_signed_fifo_handles_short_and_streaks_and_holding() -> None:
    from datetime import date
    from types import SimpleNamespace

    from finskillos.services.trade_analytics_service import _fifo_realized

    def tr(side, q, p, d):
        return SimpleNamespace(side=side, quantity=Decimal(q), price=Decimal(p), trade_date=d)

    # long round-trip (+300, 10d) then short round-trip sell-open/buy-cover (+100, 2d)
    r = _fifo_realized([
        tr("BUY", "10", "100", date(2026, 1, 1)),
        tr("SELL", "10", "130", date(2026, 1, 11)),
        tr("SELL", "5", "200", date(2026, 1, 20)),   # opens short
        tr("BUY", "5", "180", date(2026, 1, 22)),    # covers short → +100
    ])
    assert Decimal(str(r["realized_pnl"])) == Decimal("400")
    assert r["wins"] == 2 and r["avg_holding_days"] == 6.0
    assert r["max_win_streak"] == 2 and r["current_streak"] == 2

    # two consecutive losing closes → loss streak 2, current −2
    r2 = _fifo_realized([
        tr("BUY", "1", "100", date(2026, 1, 1)), tr("SELL", "1", "90", date(2026, 1, 2)),
        tr("BUY", "1", "100", date(2026, 1, 3)), tr("SELL", "1", "80", date(2026, 1, 4)),
    ])
    assert r2["max_loss_streak"] == 2 and r2["current_streak"] == -2


def test_ticker_summary_exposes_holding_and_streak() -> None:
    session = _session()
    account = _seed(session)
    s = summarize_ticker_trades(session, account.id, "NVDA")
    assert "avg_holding_days" in s and s["max_win_streak"] >= 1
    assert s["avg_holding_days"] == 4.0  # buys 06-01, sell 06-05


def test_excursion_mfe_mae_with_injected_candles() -> None:
    from types import SimpleNamespace

    from finskillos.services.trade_analytics_service import summarize_ticker_excursion

    session = _session()
    account = _seed(session)  # NVDA buys 06-01, sell 06-05

    def bars(_sym, _start):
        def bar(d, h, lo):
            return SimpleNamespace(bar_time=d, high=Decimal(h), low=Decimal(lo))
        return [
            bar(date(2026, 6, 1), "105", "98"),
            bar(date(2026, 6, 3), "130", "120"),  # peak
            bar(date(2026, 6, 5), "122", "95"),   # dip
        ]

    # NVDA = US ticker → pass fx_rate=1 so same-unit test candles aren't scaled.
    r = summarize_ticker_excursion(
        session, account.id, "NVDA", bar_fetcher=bars, fx_rate=Decimal("1")
    )
    # entry 100 (FIFO first lot); high 130 → MFE +0.30; low 95 → MAE -0.05
    assert r["avg_mfe"] == "0.3000" and r["avg_mae"] == "-0.0500"
    assert r["lots_with_bars"] == 1


def test_excursion_no_candles() -> None:
    session = _session()
    account = _seed(session)
    r = __import__(
        "finskillos.services.trade_analytics_service", fromlist=["x"]
    ).summarize_ticker_excursion(session, account.id, "NVDA", bar_fetcher=lambda *_: [])
    assert r["lots_with_bars"] == 0 and r["avg_mfe"] is None


def test_excursion_tool_registered() -> None:
    names = {t["name"] for t in TestClient(create_app()).get("/api/agent/tools").json()["tools"]}
    assert "read.trade_excursion" in names


def test_excursion_kr_ticker_no_fx_scaling() -> None:
    from types import SimpleNamespace

    from finskillos.services.trade_analytics_service import summarize_ticker_excursion

    session = _session()
    account = AccountRepository(session).create(name="M2", target_value=Decimal("1"))
    svc = TradeJournalService(session)
    for side, d, p in [("BUY", date(2026, 6, 1), "1000"), ("SELL", date(2026, 6, 5), "1100")]:
        svc.create_entry(TradeJournalInput(
            trade_date=d, ticker="005930", side=side,
            quantity=Decimal("1"), price=Decimal(p), amount=Decimal(p)))
    session.commit()

    def bars(_s, _start):
        return [SimpleNamespace(bar_time=date(2026, 6, 3), high=Decimal("1300"),
                               low=Decimal("950"))]

    # KR 6-digit → KRW candles, no FX scaling even without fx_rate passed.
    r = summarize_ticker_excursion(session, account.id, "005930", bar_fetcher=bars)
    assert r["avg_mfe"] == "0.3000"  # (1300-1000)/1000


def test_overall_stats_and_per_ticker_metrics() -> None:
    from finskillos.services.trade_analytics_service import summarize_overall_stats

    session = _session()
    account = AccountRepository(session).create(name="M3", target_value=Decimal("1"))
    svc = TradeJournalService(session)
    # 2 wins (+30,+20), 1 loss (-10)
    seq = [("NVDA", "BUY", "100"), ("NVDA", "SELL", "130"),
           ("AAPL", "BUY", "100"), ("AAPL", "SELL", "120"),
           ("MSFT", "BUY", "100"), ("MSFT", "SELL", "90")]
    for tk, side, p in seq:
        d = date(2026, 6, 1) if side == "BUY" else date(2026, 6, 5)
        svc.create_entry(TradeJournalInput(
            trade_date=d, ticker=tk, side=side,
            quantity=Decimal("1"), price=Decimal(p), amount=Decimal(p)))
    session.commit()
    st = summarize_overall_stats(session, account.id)
    assert st["closed_count"] == 3 and st["win_rate"] == round(2 / 3, 4)
    assert st["profit_factor"] == "5.000"  # 50 / 10
    assert st["expectancy"] == "13.33"     # (30+20-10)/3
    assert st["avg_win"] == "25.00" and st["avg_loss"] == "-10.00"
    # per-ticker also exposes the stats
    nvda = summarize_ticker_trades(session, account.id, "NVDA")
    assert nvda["profit_factor"] is None or "best_trade" in nvda


def test_trade_stats_tool_registered() -> None:
    names = {t["name"] for t in TestClient(create_app()).get("/api/agent/tools").json()["tools"]}
    assert "read.trade_stats" in names


def test_realized_pnl_timeseries_is_cumulative() -> None:
    from finskillos.services.trade_analytics_service import realized_pnl_timeseries

    session = _session()
    account = _seed(session)  # NVDA buys 06-01, sell 06-05 → realized 240 on 06-05
    ts = realized_pnl_timeseries(session, account.id, fx_rate=Decimal("1"))
    assert ts and ts[-1]["date"] == "2026-06-05"
    # USD realized 240 × fx_rate 1 → cumulative 240.
    assert Decimal(ts[-1]["value"]) == Decimal("240")


def test_ticker_summary_exposes_currency() -> None:
    session = _session()
    account = _seed(session)
    # NVDA has no stored currency → inferred USD (not a 6-digit KR symbol).
    assert summarize_ticker_trades(session, account.id, "NVDA")["currency"] == "USD"


def test_overall_stats_breaks_down_by_currency() -> None:
    from finskillos.services.trade_analytics_service import summarize_overall_stats

    session = _session()
    account = AccountRepository(session).create(name="M4", target_value=Decimal("1"))
    svc = TradeJournalService(session)
    # One USD ticker (+30) and one KR 6-digit ticker (+1000) → never mixed.
    seq = [
        ("NVDA", "BUY", "100", "USD"), ("NVDA", "SELL", "130", "USD"),
        ("005930", "BUY", "1000", "KRW"), ("005930", "SELL", "2000", "KRW"),
    ]
    for tk, side, p, cur in seq:
        d = date(2026, 6, 1) if side == "BUY" else date(2026, 6, 5)
        svc.create_entry(TradeJournalInput(
            trade_date=d, ticker=tk, side=side, currency=cur,
            quantity=Decimal("1"), price=Decimal(p), amount=Decimal(p)))
    session.commit()
    st = summarize_overall_stats(session, account.id)
    by_cur = st["by_currency"]
    assert Decimal(by_cur["USD"]["realized_pnl"]) == Decimal("30")
    assert Decimal(by_cur["KRW"]["realized_pnl"]) == Decimal("1000")
    assert by_cur["USD"]["closed_count"] == 1 and by_cur["KRW"]["closed_count"] == 1
