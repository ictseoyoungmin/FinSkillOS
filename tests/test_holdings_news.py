"""Holdings news (Toss × yfinance) — v4. Offline (injected client + fetcher)."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from finskillos.data_sources.adapters.yfinance_news_adapter import fetch_yf_news
from finskillos.db.base import Base
from finskillos.services.holdings_news_service import (
    sync_holdings_news,
    yahoo_symbol_for,
)
from finskillos.services.news_service import NewsArticleInput, NewsService


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_yahoo_symbol_mapping() -> None:
    assert yahoo_symbol_for("005930", "KOSPI") == "005930.KS"
    assert yahoo_symbol_for("052790", "KOSDAQ") == "052790.KQ"
    assert yahoo_symbol_for("AAPL", "NASDAQ") == "AAPL"


def test_adapter_maps_nested_content() -> None:
    raw = [
        {"id": "1", "content": {
            "title": "NNE rallies", "summary": "Nuclear names move",
            "pubDate": "2026-06-08T12:04:20Z",
            "canonicalUrl": {"url": "https://x/nne"},
            "provider": {"displayName": "Yahoo Finance"}}},
        {"id": "2", "content": {"title": "no url"}},  # dropped (no url)
    ]
    arts = fetch_yf_news("NNE", news_provider=lambda _s: raw)
    assert len(arts) == 1 and arts[0].title == "NNE rallies"
    assert arts[0].url == "https://x/nne"


class _Stub:
    def holdings(self):
        return {"items": [{"symbol": "NNE"}, {"symbol": "052790"}]}

    def stocks(self, symbols):
        return [
            {"symbol": "NNE", "market": "NASDAQ"},
            {"symbol": "052790", "market": "KOSDAQ"},
        ]


def test_sync_links_news_to_held_ticker() -> None:
    seen = []

    def fetcher(symbol, *, limit=5):
        seen.append(symbol)
        return [
            NewsArticleInput(
                title=f"{symbol} headline",
                source="Yahoo Finance",
                url=f"https://x/{symbol}",
                published_at=__import__("datetime").datetime(
                    2026, 6, 8, tzinfo=__import__("datetime").timezone.utc
                ),
                summary="body",
            )
        ]

    session = _session()
    result = sync_holdings_news(session, client=_Stub(), news_fetcher=fetcher)
    assert result["status"] == "APPLIED"
    assert result["tickers"] == 2 and result["articles"] == 2
    # KR symbol fetched with the .KQ suffix; US as-is.
    assert "052790.KQ" in seen and "NNE" in seen
    # Article linked to the held ticker (authoritative impact), not keyword-matched.
    linked = NewsService(session).list_articles_for_ticker("052790")
    assert len(linked) == 1


def test_sync_skips_when_unconfigured(monkeypatch) -> None:
    for var in ("FINSKILLOS_TOSS_CLIENT_ID", "FINSKILLOS_TOSS_CLIENT_SECRET"):
        monkeypatch.delenv(var, raising=False)
    assert sync_holdings_news(_session())["status"] == "SKIPPED"


def test_news_apply_endpoint(monkeypatch, tmp_path) -> None:
    from fastapi.testclient import TestClient

    import finskillos.services.holdings_news_service as svc
    from api.main import create_app
    from finskillos.config import reset_settings_cache

    db = f"sqlite+pysqlite:///{tmp_path / 'n.db'}"
    Base.metadata.create_all(create_engine(db, future=True))
    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", db)
    reset_settings_cache()
    monkeypatch.setattr(
        svc, "sync_holdings_news",
        lambda session: {"status": "APPLIED", "tickers": 2, "articles": 7},
    )
    body = TestClient(create_app()).post("/api/agent/sync/news/apply").json()
    assert body["status"] == "APPLIED"
    assert body["tickers"] == 2 and body["articles"] == 7
