"""Toss brokerage adapter (holdings → records) — v4 Phase 14. Offline."""

from __future__ import annotations

from finskillos.brokerage.toss.adapter import TossBrokerageAdapter
from finskillos.brokerage.toss.client import TossClient
from finskillos.brokerage.toss.config import TossConfig

_HOLDINGS = {
    "result": {
        "items": [
            {
                "symbol": "005930",
                "name": "삼성전자",
                "marketCountry": "KR",
                "currency": "KRW",
                "quantity": "100",
                "averagePurchasePrice": "65000",
                "marketValue": {"amount": "7200000"},
            },
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "marketCountry": "US",
                "currency": "USD",
                "quantity": "10",
                "averagePurchasePrice": "155.3",
                "marketValue": {"amount": "1785"},
            },
        ]
    }
}


def _cfg() -> TossConfig:
    return TossConfig("cid", "sec", "1", "https://toss.test")


def _client_with_holdings() -> TossClient:
    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 200, _HOLDINGS

    return TossClient(_cfg(), transport=transport)


def test_unavailable_when_unconfigured() -> None:
    adapter = TossBrokerageAdapter(
        TossClient(TossConfig(None, None, None, "https://x"))
    )
    assert adapter.available() is False
    assert adapter.fetch_positions() == []


def test_fetch_positions_maps_kr_and_us_holdings() -> None:
    adapter = TossBrokerageAdapter(_client_with_holdings())
    records = adapter.fetch_positions()
    by_ticker = {r["ticker"]: r for r in records}
    assert set(by_ticker) == {"005930", "AAPL"}
    assert by_ticker["005930"]["market_value"] == "7200000"
    assert by_ticker["005930"]["currency"] == "KRW"
    assert by_ticker["AAPL"]["average_cost"] == "155.3"
    assert by_ticker["AAPL"]["currency"] == "USD"


def test_fetch_cash_combines_krw_and_usd() -> None:
    from decimal import Decimal

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        if "currency=USD" in url:
            return 200, {"result": {"currency": "USD", "cashBuyingPower": "100"}}
        return 200, {"result": {"currency": "KRW", "cashBuyingPower": "7000000"}}

    adapter = TossBrokerageAdapter(TossClient(_cfg(), transport=transport))
    # 7,000,000 KRW + 100 USD * 1350 = 7,135,000
    assert adapter.fetch_cash(Decimal("1350")) == Decimal("7135000")


def test_fetch_trades_maps_closed_orders() -> None:
    page = {
        "result": {
            "orders": [
                {
                    "orderId": "o1", "symbol": "005930", "side": "BUY",
                    "orderType": "LIMIT", "status": "FILLED", "currency": "KRW",
                    "orderedAt": "2026-03-28T09:30:00+09:00",
                    "execution": {
                        "filledQuantity": "10", "averageFilledPrice": "70000",
                        "filledAmount": "700000", "commission": "1400", "tax": "0",
                        "filledAt": "2026-03-28T09:31:15+09:00",
                    },
                },
                {  # unfilled → skipped
                    "orderId": "o2", "symbol": "AAPL", "side": "SELL",
                    "status": "PENDING", "currency": "USD",
                    "execution": {"filledQuantity": "0"},
                },
            ],
            "nextCursor": None, "hasNext": False,
        }
    }

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 200, page

    recs = TossBrokerageAdapter(TossClient(_cfg(), transport=transport)).fetch_trades()
    assert len(recs) == 1
    r = recs[0]
    assert r["order_id"] == "o1" and r["ticker"] == "005930" and r["side"] == "BUY"
    assert r["trade_date"] == "2026-03-28" and r["quantity"] == "10"
    assert r["fees"] == "1400"  # commission + tax


def test_fetch_trades_propagates_closed_not_supported() -> None:
    import pytest

    from finskillos.brokerage.toss.client import TossApiError

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 400, {"error": {"code": "closed-not-supported"}}

    with pytest.raises(TossApiError):
        TossBrokerageAdapter(TossClient(_cfg(), transport=transport)).fetch_trades()


def test_no_trade_method_or_execution() -> None:
    adapter = TossBrokerageAdapter(_client_with_holdings())
    assert adapter.fetch_trades() == []  # Phase 14b
    for forbidden in ("place_order", "create_order", "buy", "sell", "execute"):
        assert not hasattr(adapter, forbidden)
    snap = adapter.snapshot()
    assert len(snap.positions) == 2 and snap.trades == []


def test_kr_symbol_passes_records_proposal() -> None:
    # KR 6-digit symbols must survive proposal_from_records (structured path).
    from decimal import Decimal

    from finskillos.agent.ingest import proposal_from_records

    adapter = TossBrokerageAdapter(_client_with_holdings())
    proposal = proposal_from_records(
        adapter.fetch_positions(), usd_krw_rate=Decimal("1350")
    )
    tickers = {r.ticker for r in proposal.rows}
    assert "005930" in tickers  # KR kept
    aapl = next(r for r in proposal.rows if r.ticker == "AAPL")
    assert aapl.market_value == "2409750"  # 1785 USD * 1350 → KRW
