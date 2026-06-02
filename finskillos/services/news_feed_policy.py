"""News feed selection policy shared by worker and System Ops."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from urllib.parse import urlencode

from finskillos.runtime_settings import read_runtime_csv, read_runtime_value

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
    runtime_overrides: Mapping[str, str] | None = None,
) -> NewsFeedPolicy:
    """Return RSS feed URLs for the current news refresh context."""

    explicit_feeds = read_runtime_csv(
        "FINSKILLOS_NEWS_RSS_FEEDS",
        runtime_overrides=runtime_overrides,
    )
    source = read_runtime_value(
        "FINSKILLOS_NEWS_RSS_SOURCE",
        default=None,
        runtime_overrides=runtime_overrides,
    )
    language = read_runtime_value(
        "FINSKILLOS_NEWS_RSS_LANGUAGE",
        default="en-US",
        include_empty=True,
        runtime_overrides=runtime_overrides,
    )
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
            *read_runtime_csv("FINSKILLOS_NEWS_RSS_TICKERS"),
            *read_runtime_csv("FINSKILLOS_MARKET_REFRESH_TICKERS"),
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
