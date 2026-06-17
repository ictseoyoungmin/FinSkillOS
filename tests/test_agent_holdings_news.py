"""Agent holdings-news tooling — importance ranking + refresh protocol. Offline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from fastapi.testclient import TestClient

from api.main import create_app
from finskillos.agent.context import _news_importance
from finskillos.agent.ingest import parse_protocol_request, parse_protocol_requests


def _impact(**kw) -> SimpleNamespace:
    base = {"impact_score": Decimal("0"), "risk_level": "UNKNOWN",
            "sentiment_label": "UNKNOWN", "ticker": "NNE"}
    base.update(kw)
    return SimpleNamespace(**base)


def _article(days_ago: int) -> SimpleNamespace:
    return SimpleNamespace(
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=days_ago),
        title="t", source="Yahoo Finance",
    )


def test_importance_orders_risk_and_recency_first() -> None:
    fresh_risky = _news_importance(_article(0), [_impact(risk_level="RED")])
    old_quiet = _news_importance(_article(20), [_impact()])
    assert fresh_risky > old_quiet
    # negative sentiment outranks neutral, all else equal
    neg = _news_importance(_article(1), [_impact(sentiment_label="NEGATIVE")])
    neu = _news_importance(_article(1), [_impact(sentiment_label="NEUTRAL")])
    assert neg > neu


def test_holdings_news_protocol_intent() -> None:
    assert parse_protocol_request("내 보유 주식 뉴스 갱신해줘") == "refresh_holdings_news"
    assert parse_protocol_request("refresh holdings news") == "refresh_holdings_news"
    # generic news refresh is NOT mistaken for holdings news
    assert parse_protocol_request("refresh news") == "refresh_news"
    assert "refresh_holdings_news" in parse_protocol_requests("보유종목 뉴스 갱신")


def test_holdings_sectors_protocol_intent() -> None:
    assert parse_protocol_request("섹터 분류해줘") == "refresh_holdings_sectors"
    assert parse_protocol_request("classify my sectors") == "refresh_holdings_sectors"
    assert parse_protocol_request("보유 섹터 채워줘") == "refresh_holdings_sectors"
    # sector intent is not mistaken for holdings-news refresh
    assert parse_protocol_request("update holdings news") == "refresh_holdings_news"


def test_refresh_holdings_news_in_tool_catalogue() -> None:
    body = TestClient(create_app()).get("/api/agent/tools").json()
    names = {t["name"] for t in body["tools"]}
    assert "ops.refresh_holdings_news" in names
    tool = next(t for t in body["tools"] if t["name"] == "ops.refresh_holdings_news")
    assert tool["category"] == "ops" and tool["method"] == "POST"


def test_refresh_holdings_news_route_exists() -> None:
    # Fixture-first (no DB in tests) → 200 with the acknowledgement shell.
    res = TestClient(create_app()).post("/api/system-ops/refresh-holdings-news")
    assert res.status_code == 200


def test_materiality_keyword_boosts_importance() -> None:
    from finskillos.agent.context import _news_importance
    earnings = _news_importance(_article(0), [_impact()])  # _article title is "t"
    # an earnings headline outscores a plain same-age one
    from datetime import datetime, timezone
    from types import SimpleNamespace
    def art(title):
        return SimpleNamespace(title=title, published_at=datetime.now(tz=timezone.utc))
    assert _news_importance(art("Oracle Q4 earnings beat"), [_impact()]) > _news_importance(
        art("Oracle hosts a conference"), [_impact()]
    )
    assert earnings >= 0.0


def test_dedupe_drops_same_wire_story() -> None:
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from finskillos.agent.context import _dedupe_news
    def art(title):
        return SimpleNamespace(title=title, published_at=datetime.now(tz=timezone.utc))
    rows = [
        (art("Tech stocks today chip stocks pull back hard"), [_impact()]),
        (art("Tech stocks today chip stocks pull back fast"), [_impact()]),
        (art("Oracle earnings beat estimates"), [_impact()]),
    ]
    assert len(_dedupe_news(rows)) == 2  # first two share the first 6 words


def test_toss_sync_protocol_intents() -> None:
    assert parse_protocol_request("토스에서 포트폴리오 동기화해줘") == "sync_toss_holdings"
    assert parse_protocol_request("sync holdings from toss") == "sync_toss_holdings"
    assert parse_protocol_request("토스 동기화해줘") == "sync_toss_holdings"
    assert parse_protocol_request("토스 거래 동기화") == "sync_toss_trades"
    assert parse_protocol_request("sync trades from toss") == "sync_toss_trades"
    # Toss is the portfolio source, so "포트폴리오 업데이트" (no "toss" word) syncs.
    assert parse_protocol_request("포트폴리오 정보 업데이트") == "sync_toss_holdings"
    assert parse_protocol_request("포트폴리오 갱신해줘") == "sync_toss_holdings"
    assert parse_protocol_request("보유 종목 동기화") == "sync_toss_holdings"
    assert parse_protocol_request("update my portfolio") == "sync_toss_holdings"
    # news refresh is not mistaken for a portfolio sync
    assert parse_protocol_request("보유 뉴스 갱신") == "refresh_holdings_news"
    assert parse_protocol_request("포트폴리오 뉴스 갱신") == "refresh_holdings_news"
    assert parse_protocol_request("refresh holdings news") == "refresh_holdings_news"


def test_toss_sync_tools_and_routes() -> None:
    client = TestClient(create_app())
    names = {t["name"] for t in client.get("/api/agent/tools").json()["tools"]}
    assert {"ops.sync_toss_holdings", "ops.sync_toss_trades"} <= names
    for path in ("/api/system-ops/sync-toss-holdings", "/api/system-ops/sync-toss-trades"):
        assert client.post(path).status_code == 200  # fixture-first shell (no DB)
