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
