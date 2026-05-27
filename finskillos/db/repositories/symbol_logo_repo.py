"""Repository for cached ticker logo metadata."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from finskillos.db.models import SymbolLogoCache

UTC = timezone.utc


class SymbolLogoRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, ticker: str) -> SymbolLogoCache | None:
        stmt = select(SymbolLogoCache).where(
            SymbolLogoCache.ticker == _normalize_ticker(ticker)
        )
        return self.session.scalars(stmt).one_or_none()

    def upsert_provider_logo(
        self,
        ticker: str,
        *,
        provider: str,
        logo_url: str,
    ) -> SymbolLogoCache:
        normalized = _normalize_ticker(ticker)
        row = self.get(normalized)
        now = datetime.now(tz=UTC)
        if row is None:
            row = SymbolLogoCache(
                ticker=normalized,
                provider=provider,
                logo_url=logo_url,
                fetched_at=now,
            )
            self.session.add(row)
        else:
            row.provider = provider
            row.logo_url = logo_url
            row.fetched_at = now
        self.session.flush()
        return row


def _normalize_ticker(ticker: str) -> str:
    return ticker.strip().upper()
