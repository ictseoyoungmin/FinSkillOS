"""News adapter protocol — Slice 10.

Mirrors the ``BaseMarketDataAdapter`` pattern from Slice 04. Concrete
providers (RSS, vendor APIs, …) only need to implement
``fetch_latest`` returning a sequence of ``NewsArticleInput`` rows;
the service layer takes care of upsert + classification.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from finskillos.services.news_service import NewsArticleInput


class NewsDataFetchError(RuntimeError):
    """Raised when a news adapter cannot fetch or parse provider data."""


@runtime_checkable
class BaseNewsAdapter(Protocol):
    def fetch_latest(self) -> Sequence[NewsArticleInput]: ...


__all__ = ["BaseNewsAdapter", "NewsDataFetchError"]
