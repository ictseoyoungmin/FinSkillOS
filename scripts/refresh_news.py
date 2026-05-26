"""Refresh stored news articles from a configured adapter.

Manual-first, cron-compatible command for the News Intelligence provider
boundary. The command stores only source/title/link/published/short
summary metadata through ``NewsService``; it does not crawl article bodies.

Examples:
    python3 scripts/refresh_news.py --adapter rss --feed-url https://example.com/rss
    python3 scripts/refresh_news.py --adapter rss --feed-file tests/fixtures/feed.xml
"""

from __future__ import annotations

# ruff: noqa: E402, I001

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finskillos.config import get_settings
from finskillos.data_sources.adapters.rss_news_adapter import RssFeed, RssNewsAdapter
from finskillos.db.session import session_scope
from finskillos.logging_config import setup_logging
from finskillos.services.news_service import NewsArticleInput, NewsService

logger = logging.getLogger("finskillos.scripts.refresh_news")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh stored news articles from configured feeds."
    )
    parser.add_argument(
        "--adapter",
        choices=("rss",),
        default="rss",
        help="News adapter to use. `rss` supports RSS 2.0 and Atom feeds.",
    )
    parser.add_argument(
        "--feed-url",
        action="append",
        default=[],
        help="RSS/Atom feed URL. Repeat to ingest multiple feeds.",
    )
    parser.add_argument(
        "--feed-file",
        action="append",
        type=Path,
        default=[],
        help="Local RSS/Atom XML file for offline refresh/test runs.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Optional source label override applied to all configured feeds.",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Optional language override applied to all configured feeds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable summary.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    setup_logging(settings.log_level)

    feeds = _rss_feeds(
        urls=args.feed_url,
        files=args.feed_file,
        source=args.source,
        language=args.language,
    )
    if not feeds:
        raise SystemExit("--feed-url or --feed-file is required for --adapter rss")

    adapter = RssNewsAdapter(
        feeds,
        fetcher=_file_fetcher(args.feed_file) if args.feed_file else None,
    )
    articles = tuple(adapter.fetch_latest())
    ingested = _ingest(articles)

    summary = {
        "adapter": args.adapter,
        "feeds": len(feeds),
        "articlesSeen": len(articles),
        "articlesIngested": ingested,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    else:
        logger.info("News refresh summary: %s", summary)
    return 0


def _rss_feeds(
    *,
    urls: list[str],
    files: list[Path],
    source: str | None,
    language: str | None,
) -> tuple[RssFeed, ...]:
    if urls and files:
        raise SystemExit("Use either --feed-url or --feed-file, not both")
    values = urls or [path.resolve().as_uri() for path in files]
    return tuple(RssFeed(url=value, source=source, language=language) for value in values)


def _file_fetcher(files: list[Path]):
    by_uri = {path.resolve().as_uri(): path for path in files}

    def fetch(url: str) -> str:
        path = by_uri.get(url)
        if path is None:
            raise ValueError(f"no local feed file registered for {url}")
        return path.read_text(encoding="utf-8")

    return fetch


def _ingest(articles: tuple[NewsArticleInput, ...]) -> int:
    with session_scope() as session:
        service = NewsService(session)
        for article in articles:
            service.ingest_article(article)
    return len(articles)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
