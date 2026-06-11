"""yfinance per-ticker news adapter — v4.

Fetches the latest news for one Yahoo symbol via the (unofficial) yfinance
library and maps it into the canonical ``NewsArticleInput``. Read-only. The raw
news provider is injectable so tests run offline (no network).

yfinance 1.x returns nested items: ``{"id", "content": {title, summary, pubDate,
canonicalUrl: {url}, provider: {displayName}}}``.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from finskillos.services.news_service import NewsArticleInput

__all__ = ["fetch_yf_news"]

_MAX_TITLE = 240
_MAX_SUMMARY = 600


def _yf_news_provider(symbol: str) -> list:
    import yfinance as yf

    return yf.Ticker(symbol).news or []


def _parse_dt(value) -> datetime:
    if not value:
        return datetime.now(tz=timezone.utc)
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(tz=timezone.utc)


def _url(content: dict) -> str | None:
    for key in ("canonicalUrl", "clickThroughUrl"):
        block = content.get(key)
        if isinstance(block, dict) and block.get("url"):
            return str(block["url"])
    return None


def fetch_yf_news(
    symbol: str,
    *,
    limit: int = 8,
    news_provider: Callable[[str], list] | None = None,
) -> list[NewsArticleInput]:
    """Latest news for a Yahoo ``symbol`` → ``NewsArticleInput`` list."""

    raw = (news_provider or _yf_news_provider)(symbol) or []
    articles: list[NewsArticleInput] = []
    for item in raw[:limit]:
        content = item.get("content") if isinstance(item, dict) else None
        if not isinstance(content, dict):
            continue
        title = str(content.get("title") or "").strip()
        url = _url(content)
        if not title or not url:
            continue
        provider = content.get("provider")
        source = (
            provider.get("displayName")
            if isinstance(provider, dict)
            else None
        ) or "Yahoo Finance"
        summary = str(content.get("summary") or content.get("description") or title)
        articles.append(
            NewsArticleInput(
                title=title[:_MAX_TITLE],
                source=str(source),
                url=url,
                published_at=_parse_dt(content.get("pubDate")),
                summary=summary[:_MAX_SUMMARY],
            )
        )
    return articles
