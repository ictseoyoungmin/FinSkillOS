"""Toss client + OAuth — v4 Phase 13. Offline (injected transport / clock)."""

from __future__ import annotations

import pytest

from finskillos.brokerage.toss.auth import TossTokenManager
from finskillos.brokerage.toss.client import (
    TossApiError,
    TossClient,
    TossNotConfigured,
)
from finskillos.brokerage.toss.config import TossConfig, load_toss_config


def _cfg(**kw) -> TossConfig:
    base = {
        "client_id": "cid",
        "client_secret": "sec",
        "account_seq": "1",
        "base_url": "https://toss.test",
    }
    base.update(kw)
    return TossConfig(**base)


def _token_transport(method, url, headers, body):
    if url.endswith("/oauth2/token"):
        return 200, {"access_token": "TKN", "expires_in": 3600, "token_type": "Bearer"}
    return 200, {"result": {"ok": True}}


def test_config_disabled_when_unset(monkeypatch) -> None:
    for var in (
        "FINSKILLOS_TOSS_CLIENT_ID",
        "FINSKILLOS_TOSS_CLIENT_SECRET",
        "FINSKILLOS_TOSS_ACCOUNT_SEQ",
    ):
        monkeypatch.delenv(var, raising=False)
    assert load_toss_config().configured is False
    assert TossClient(load_toss_config()).available() is False


def test_token_issued_cached_and_reissued() -> None:
    now = [1000.0]
    calls = {"n": 0}

    def transport(method, url, headers, body):
        calls["n"] += 1
        return 200, {"access_token": f"T{calls['n']}", "expires_in": 100}

    mgr = TossTokenManager(_cfg(), transport=transport, clock=lambda: now[0])
    assert mgr.token() == "T1"
    assert mgr.token() == "T1"  # cached
    assert calls["n"] == 1
    now[0] += 200  # past expiry (− skew)
    assert mgr.token() == "T2"  # reissued


def test_unconfigured_token_is_none() -> None:
    mgr = TossTokenManager(_cfg(client_id=None), transport=_token_transport)
    assert mgr.token() is None


def test_get_sends_bearer_and_account_header_and_unwraps_result() -> None:
    seen = []

    def transport(method, url, headers, body):
        seen.append((url, dict(headers)))
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 200, {"result": {"items": [1, 2]}}

    client = TossClient(_cfg(), transport=transport)
    assert client.holdings() == {"items": [1, 2]}
    holdings = next(h for h in seen if h[0].endswith("/holdings"))
    assert holdings[1]["Authorization"] == "Bearer TKN"
    assert holdings[1]["X-Tossinvest-Account"] == "1"


def test_401_triggers_one_reissue_then_succeeds() -> None:
    state = {"calls": 0}

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        state["calls"] += 1
        if state["calls"] == 1:
            return 401, {"error": "expired"}
        return 200, {"result": {"ok": True}}

    client = TossClient(_cfg(), transport=transport)
    assert client.accounts() == {"ok": True}
    assert state["calls"] == 2


def test_429_backs_off_once() -> None:
    slept = []
    state = {"calls": 0}

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        state["calls"] += 1
        return (429, {"error": "rate"}) if state["calls"] == 1 else (200, {"result": 5})

    client = TossClient(_cfg(), transport=transport, sleep=slept.append)
    assert client.exchange_rate() == 5
    assert slept == [1.0]


def test_account_required_raises_without_account_seq() -> None:
    client = TossClient(_cfg(account_seq=None), transport=_token_transport)
    with pytest.raises(TossNotConfigured):
        client.holdings()


def test_api_error_raised_on_4xx() -> None:
    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 400, {"error": "bad"}

    with pytest.raises(TossApiError):
        TossClient(_cfg(), transport=transport).accounts()


def test_orders_closed_builds_paginated_query() -> None:
    seen = []

    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        seen.append(url)
        return 200, {"result": {"orders": [], "nextCursor": None, "hasNext": False}}

    client = TossClient(_cfg(), transport=transport)
    client.orders(
        status="CLOSED",
        from_date="2026-03-01",
        to_date="2026-03-31",
        cursor="c1",
        limit=50,
    )
    url = seen[0]
    assert "status=CLOSED" in url
    assert "from=2026-03-01" in url and "to=2026-03-31" in url
    assert "cursor=c1" in url and "limit=50" in url


def test_orders_closed_returns_executed_orders() -> None:
    def transport(method, url, headers, body):
        if url.endswith("/oauth2/token"):
            return 200, {"access_token": "TKN", "expires_in": 3600}
        return 200, {
            "result": {
                "orders": [{"orderId": "o1", "status": "FILLED"}],
                "nextCursor": None,
                "hasNext": False,
            }
        }

    result = TossClient(_cfg(), transport=transport).orders(status="CLOSED")
    assert result["orders"][0]["status"] == "FILLED"


def test_client_has_no_order_write_methods() -> None:
    client = TossClient(_cfg(), transport=_token_transport)
    for forbidden in (
        "create_order",
        "place_order",
        "submit_order",
        "modify_order",
        "cancel_order",
        "buy",
        "sell",
    ):
        assert not hasattr(client, forbidden), forbidden
