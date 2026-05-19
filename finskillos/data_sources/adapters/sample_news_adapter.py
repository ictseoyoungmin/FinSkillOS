"""Deterministic in-memory news adapter — Slice 10 test/seed helper.

Used by the test suite (and optional manual seed flows) to feed
``NewsService.ingest_article`` without any live HTTP. Live providers
plug in later behind the same ``BaseNewsAdapter`` protocol declared in
``finskillos.data_sources.news_adapter``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from finskillos.data_sources.news_adapter import BaseNewsAdapter
from finskillos.services.news_service import NewsArticleInput


class MockNewsAdapter(BaseNewsAdapter):
    """Returns a fixed in-memory list of ``NewsArticleInput`` rows."""

    def __init__(self, articles: Iterable[NewsArticleInput] = ()) -> None:
        self._articles: tuple[NewsArticleInput, ...] = tuple(articles)

    def fetch_latest(self) -> Sequence[NewsArticleInput]:
        return self._articles
