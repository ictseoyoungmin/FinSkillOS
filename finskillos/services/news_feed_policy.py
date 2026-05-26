"""News feed selection policy shared by worker and System Ops."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urlencode

DEFAULT_NEWS_TICKERS: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "TSLA")


@dataclass(frozen=True)
class NewsFeedPolicy:
    feeds: tuple[str, ...]
    tickers: tuple[str, ...]
    source: str | None = None
    language: str | None = None
    generated: bool = False

    @property
    def available(self) -> bool:
        return bool(self.feeds)


def build_news_feed_policy(
    *,
    subscribed_tickers: Iterable[str] = (),
) -> NewsFeedPolicy:
    """Return RSS feed URLs for the current news refresh context."""

    explicit_feeds = _csv_env("FINSKILLOS_NEWS_RSS_FEEDS")
    source = os.getenv("FINSKILLOS_NEWS_RSS_SOURCE") or None
    language = os.getenv("FINSKILLOS_NEWS_RSS_LANGUAGE") or "en-US"
    tickers = _ticker_policy(subscribed_tickers)

    if explicit_feeds:
        return NewsFeedPolicy(
            feeds=explicit_feeds,
            tickers=tickers,
            source=source,
            language=language,
            generated=False,
        )

    return NewsFeedPolicy(
        feeds=(_google_news_feed(tickers),) if tickers else (),
        tickers=tickers,
        source=source,
        language=language,
        generated=True,
    )


def _ticker_policy(subscribed_tickers: Iterable[str]) -> tuple[str, ...]:
    return _dedupe_tickers(
        (
            *_clean_tickers(subscribed_tickers),
            *_csv_env("FINSKILLOS_NEWS_RSS_TICKERS"),
            *_csv_env("FINSKILLOS_MARKET_REFRESH_TICKERS"),
            *DEFAULT_NEWS_TICKERS,
        )
    )


def _google_news_feed(tickers: tuple[str, ...]) -> str:
    query = " OR ".join(tickers)
    params = urlencode(
        {
            "q": f"{query} stock",
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )
    return f"https://news.google.com/rss/search?{params}"


def _csv_env(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    return tuple(part.strip() for part in raw.replace(";", ",").split(",") if part.strip())


def _clean_tickers(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(value.strip().upper() for value in values if value and value.strip())


def _dedupe_tickers(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in _clean_tickers(values):
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


__all__ = ["DEFAULT_NEWS_TICKERS", "NewsFeedPolicy", "build_news_feed_policy"]
