"""Shared ticker-logo resolution for API surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from sqlalchemy.orm import Session

from finskillos.config import get_settings
from finskillos.db.repositories import SymbolLogoRepository

LOGO_DEV_TICKER_BASE_URL = "https://img.logo.dev/ticker"
LOGO_DEV_PROVIDER = "logo_dev"
LOCAL_LOGO_ONLY_TICKERS = frozenset(
    {
        "SPY",
        "QQQ",
        "DIA",
        "IWM",
        "SMH",
        "SOXX",
        "XLK",
        "VIX",
        "US10Y",
        "DXY",
    }
)


@dataclass(frozen=True)
class SymbolLogoIdentity:
    ticker: str
    name: str
    logo_url: str | None
    logo_source: str
    avatar_text: str
    brand_color: str


def resolve_symbol_logo_identity(
    session: Session | None,
    *,
    ticker: str,
    name: str,
    avatar_text: str,
    brand_color: str,
) -> SymbolLogoIdentity:
    normalized = ticker.strip().upper()
    fallback = SymbolLogoIdentity(
        ticker=normalized,
        name=name,
        logo_url=None,
        logo_source="local_fallback",
        avatar_text=avatar_text,
        brand_color=brand_color,
    )
    if session is None:
        return fallback
    if normalized in LOCAL_LOGO_ONLY_TICKERS:
        return fallback

    repo = SymbolLogoRepository(session)
    cached = repo.get(normalized)
    if cached is not None:
        return SymbolLogoIdentity(
            ticker=normalized,
            name=name,
            logo_url=cached.logo_url,
            logo_source="provider_cache",
            avatar_text=avatar_text,
            brand_color=brand_color,
        )

    settings = get_settings()
    if settings.logo_provider != LOGO_DEV_PROVIDER or not settings.logo_dev_token:
        return fallback

    logo_url = logo_dev_ticker_url(normalized, settings.logo_dev_token)
    repo.upsert_provider_logo(
        normalized,
        provider=LOGO_DEV_PROVIDER,
        logo_url=logo_url,
    )
    return SymbolLogoIdentity(
        ticker=normalized,
        name=name,
        logo_url=logo_url,
        logo_source="provider_cache",
        avatar_text=avatar_text,
        brand_color=brand_color,
    )


def logo_dev_ticker_url(ticker: str, token: str) -> str:
    symbol = quote(ticker.strip().upper(), safe=".")
    publishable_token = quote(token.strip(), safe="")
    return (
        f"{LOGO_DEV_TICKER_BASE_URL}/{symbol}"
        f"?token={publishable_token}&format=png&size=96"
    )
