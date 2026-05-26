"""RSS / Atom adapter tests for News Intelligence provider ingestion."""

from __future__ import annotations

from datetime import timezone

import pytest

from finskillos.data_sources.adapters.rss_news_adapter import RssFeed, RssNewsAdapter
from finskillos.data_sources.news_adapter import NewsDataFetchError
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS

RSS_FEED = """\
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Market Desk</title>
    <language>en-US</language>
    <item>
      <title>TSLA delivery numbers top expectations</title>
      <link>https://news.example.com/tsla-deliveries</link>
      <pubDate>Tue, 26 May 2026 12:30:00 GMT</pubDate>
      <description><![CDATA[<p>TSLA delivery update was <b>strong</b>.</p>]]></description>
      <source url="https://finance.example.com">Finance Wire</source>
      <dc:creator>Market Desk Team</dc:creator>
    </item>
    <item>
      <title>Missing link is skipped</title>
      <description>There is no URL here.</description>
    </item>
  </channel>
</rss>
"""


ATOM_FEED = """\
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en">
  <title>Macro Wire</title>
  <entry>
    <title>Fed minutes keep yields in focus</title>
    <link href="https://news.example.com/fed-minutes" rel="alternate" />
    <updated>2026-05-26T13:45:00Z</updated>
    <summary>FOMC discussion kept Treasury yields in focus.</summary>
    <author><name>Macro Team</name></author>
  </entry>
</feed>
"""


def test_rss_adapter_normalizes_entries_without_article_bodies() -> None:
    adapter = RssNewsAdapter(
        [RssFeed(url="https://feeds.example.com/markets.xml")],
        fetcher=lambda _url: RSS_FEED,
    )

    rows = adapter.fetch_latest()

    assert len(rows) == 1
    row = rows[0]
    assert row.title == "TSLA delivery numbers top expectations"
    assert row.source == "Finance Wire"
    assert row.url == "https://news.example.com/tsla-deliveries"
    assert row.published_at.tzinfo == timezone.utc
    assert row.published_at.isoformat() == "2026-05-26T12:30:00+00:00"
    assert row.summary == "TSLA delivery update was strong."
    assert "<p>" not in row.summary
    assert row.author == "Market Desk Team"
    assert row.language == "en-US"


def test_atom_adapter_supports_source_override_and_author() -> None:
    adapter = RssNewsAdapter(
        [RssFeed(url="https://feeds.example.com/macro.atom", source="Fed Feed")],
        fetcher=lambda _url: ATOM_FEED,
    )

    rows = adapter.fetch_latest()

    assert len(rows) == 1
    row = rows[0]
    assert row.title == "Fed minutes keep yields in focus"
    assert row.source == "Fed Feed"
    assert row.url == "https://news.example.com/fed-minutes"
    assert row.published_at.isoformat() == "2026-05-26T13:45:00+00:00"
    assert row.summary == "FOMC discussion kept Treasury yields in focus."
    assert row.author == "Macro Team"
    assert row.language == "en"


def test_rss_adapter_clips_provider_text_before_service_ingest() -> None:
    long_title = "T" * (MAX_TITLE_CHARS + 10)
    long_summary = "S" * (MAX_SUMMARY_CHARS + 10)
    feed = f"""\
<rss version="2.0">
  <channel>
    <item>
      <title>{long_title}</title>
      <link>https://news.example.com/long</link>
      <description>{long_summary}</description>
    </item>
  </channel>
</rss>
"""
    adapter = RssNewsAdapter(["https://feeds.example.com/long.xml"], fetcher=lambda _: feed)

    row = adapter.fetch_latest()[0]

    assert len(row.title) == MAX_TITLE_CHARS
    assert len(row.summary) == MAX_SUMMARY_CHARS


def test_rss_adapter_raises_adapter_error_for_bad_xml() -> None:
    adapter = RssNewsAdapter(["https://feeds.example.com/bad.xml"], fetcher=lambda _: "<rss>")

    with pytest.raises(NewsDataFetchError, match="parse failed"):
        adapter.fetch_latest()
