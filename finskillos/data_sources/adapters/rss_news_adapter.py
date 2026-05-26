"""RSS / Atom news adapter.

The adapter intentionally returns only provider metadata plus a short
summary. It never attempts to download full article bodies; the
``NewsService`` remains responsible for DB-safe truncation and impact
classification.
"""

from __future__ import annotations

import html
import re
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from xml.etree import ElementTree

from finskillos.data_sources.news_adapter import BaseNewsAdapter, NewsDataFetchError
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS
from finskillos.services.news_service import NewsArticleInput

UTC = timezone.utc
FeedFetcher = Callable[[str], str | bytes]

_ATOM_NS = "{http://www.w3.org/2005/Atom}"
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_PUNCTUATION_SPACE_RE = re.compile(r"\s+([,.;:!?])")


@dataclass(frozen=True)
class RssFeed:
    """One configured feed source."""

    url: str
    source: str | None = None
    language: str | None = None


class RssNewsAdapter(BaseNewsAdapter):
    """Normalize RSS / Atom entries into ``NewsArticleInput`` rows."""

    def __init__(
        self,
        feeds: Sequence[str | RssFeed],
        *,
        fetcher: FeedFetcher | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._feeds = tuple(_coerce_feed(feed) for feed in feeds)
        self._timeout_seconds = timeout_seconds
        self._fetcher = fetcher or self._fetch_url

    def fetch_latest(self) -> Sequence[NewsArticleInput]:
        articles: list[NewsArticleInput] = []
        for feed in self._feeds:
            xml_text = self._fetcher(feed.url)
            articles.extend(_parse_feed(xml_text, feed=feed))
        return tuple(articles)

    def _fetch_url(self, url: str) -> bytes:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "FinSkillOS/1.0 RSS adapter; summaries only",
                "Accept": "application/rss+xml, application/atom+xml, application/xml",
            },
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - user-configured feed URL.
                request,
                timeout=self._timeout_seconds,
            ) as response:
                return response.read()
        except OSError as exc:
            raise NewsDataFetchError(f"news feed fetch failed: {url}") from exc


def _coerce_feed(feed: str | RssFeed) -> RssFeed:
    if isinstance(feed, RssFeed):
        return feed
    return RssFeed(url=feed)


def _parse_feed(xml_text: str | bytes, *, feed: RssFeed) -> tuple[NewsArticleInput, ...]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise NewsDataFetchError(f"news feed parse failed: {feed.url}") from exc

    if root.tag == "rss" or root.find("channel") is not None:
        return _parse_rss(root, feed=feed)
    if _strip_ns(root.tag) == "feed":
        return _parse_atom(root, feed=feed)
    raise NewsDataFetchError(f"unsupported news feed format: {feed.url}")


def _parse_rss(root: ElementTree.Element, *, feed: RssFeed) -> tuple[NewsArticleInput, ...]:
    channel = root.find("channel") or root
    channel_source = feed.source or _text(channel, "title") or _source_from_url(feed.url)
    language = feed.language or _text(channel, "language")

    articles: list[NewsArticleInput] = []
    for item in channel.findall("item"):
        title = _clean_text(_text(item, "title"))
        url = _clean_text(_text(item, "link")) or _clean_text(_text(item, "guid"))
        if not title or not url:
            continue
        articles.append(
            NewsArticleInput(
                title=_clip(title, MAX_TITLE_CHARS),
                source=_clean_text(_text(item, "source")) or channel_source,
                url=url,
                published_at=_parse_datetime(
                    _text(item, "pubDate") or _text(item, "published")
                ),
                summary=_clip(
                    _clean_text(
                        _text(item, "description")
                        or _text(item, "summary")
                        or title
                    ),
                    MAX_SUMMARY_CHARS,
                ),
                author=_clean_text(_text(item, "author") or _text(item, "dc:creator")),
                language=language,
            )
        )
    return tuple(articles)


def _parse_atom(root: ElementTree.Element, *, feed: RssFeed) -> tuple[NewsArticleInput, ...]:
    source = feed.source or _atom_text(root, "title") or _source_from_url(feed.url)
    language = feed.language or root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")

    articles: list[NewsArticleInput] = []
    for entry in root.findall(f"{_ATOM_NS}entry"):
        title = _clean_text(_atom_text(entry, "title"))
        url = _atom_link(entry) or _clean_text(_atom_text(entry, "id"))
        if not title or not url:
            continue
        articles.append(
            NewsArticleInput(
                title=_clip(title, MAX_TITLE_CHARS),
                source=source,
                url=url,
                published_at=_parse_datetime(
                    _atom_text(entry, "published") or _atom_text(entry, "updated")
                ),
                summary=_clip(
                    _clean_text(
                        _atom_text(entry, "summary")
                        or _atom_text(entry, "content")
                        or title
                    ),
                    MAX_SUMMARY_CHARS,
                ),
                author=_atom_author(entry),
                language=language,
            )
        )
    return tuple(articles)


def _text(element: ElementTree.Element, tag: str) -> str:
    try:
        found = element.find(tag)
    except SyntaxError:
        found = None
    if found is None and ":" in tag:
        local_name = tag.split(":", 1)[1]
        found = next(
            (child for child in element if _strip_ns(child.tag) == local_name),
            None,
        )
    return found.text if found is not None and found.text is not None else ""


def _atom_text(element: ElementTree.Element, tag: str) -> str:
    found = element.find(f"{_ATOM_NS}{tag}")
    return found.text if found is not None and found.text is not None else ""


def _atom_link(entry: ElementTree.Element) -> str:
    fallback = ""
    for link in entry.findall(f"{_ATOM_NS}link"):
        href = link.attrib.get("href", "").strip()
        if not href:
            continue
        if link.attrib.get("rel", "alternate") == "alternate":
            return href
        fallback = fallback or href
    return fallback


def _atom_author(entry: ElementTree.Element) -> str | None:
    author = entry.find(f"{_ATOM_NS}author")
    if author is None:
        return None
    return _clean_text(_atom_text(author, "name")) or None


def _parse_datetime(value: str) -> datetime:
    raw = value.strip()
    if not raw:
        return datetime.now(tz=UTC)
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(tz=UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = _HTML_TAG_RE.sub(" ", value)
    cleaned = _WHITESPACE_RE.sub(" ", html.unescape(without_tags)).strip()
    return _PUNCTUATION_SPACE_RE.sub(r"\1", cleaned)


def _clip(value: str, max_chars: int) -> str:
    return value[:max_chars]


def _source_from_url(url: str) -> str:
    host = urlparse(url).netloc
    return host or "rss"


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


__all__ = ["RssFeed", "RssNewsAdapter"]
