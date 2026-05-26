"""News feed policy tests."""

from __future__ import annotations

from finskillos.services.news_feed_policy import build_news_feed_policy


def test_news_feed_policy_prefers_explicit_feeds(monkeypatch) -> None:
    monkeypatch.setenv("FINSKILLOS_NEWS_RSS_FEEDS", "https://feed.example/a.xml")
    monkeypatch.setenv("FINSKILLOS_NEWS_RSS_TICKERS", "AAPL,MSFT")

    policy = build_news_feed_policy(subscribed_tickers=("NVDA",))

    assert policy.feeds == ("https://feed.example/a.xml",)
    assert policy.tickers[:3] == ("NVDA", "AAPL", "MSFT")
    assert policy.generated is False


def test_news_feed_policy_generates_google_feed_from_tickers(monkeypatch) -> None:
    monkeypatch.delenv("FINSKILLOS_NEWS_RSS_FEEDS", raising=False)
    monkeypatch.setenv("FINSKILLOS_NEWS_RSS_TICKERS", "AAPL,MSFT")

    policy = build_news_feed_policy(subscribed_tickers=("TSLA",))

    assert policy.generated is True
    assert len(policy.feeds) == 1
    assert policy.feeds[0].startswith("https://news.google.com/rss/search?")
    assert "TSLA+OR+AAPL+OR+MSFT" in policy.feeds[0]
