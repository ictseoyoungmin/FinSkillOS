"""Health and freshness probes for the React shell."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter
from pydantic import Field
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from api.schemas.common import CamelModel

router = APIRouter(tags=["health"])


class HealthResponse(CamelModel):
    status: str
    service: str
    mode: str
    generated_at: datetime


class ProtocolAvailability(CamelModel):
    key: str
    status: Literal["AVAILABLE", "NOOP", "UNAVAILABLE"]
    detail: str


class SystemStatusResponse(CamelModel):
    generated_at: datetime
    mode: str
    api_status: Literal["LIVE"]
    db_status: Literal["LIVE", "MISSING"]
    source: Literal["fixture", "live"]
    data_completeness: Literal["complete", "partial", "missing"]
    latest_portfolio_snapshot_at: str | None = None
    latest_market_bar_at: str | None = None
    latest_indicator_at: str | None = None
    latest_regime_at: str | None = None
    latest_news_at: str | None = None
    latest_event_at: str | None = None
    stale_flags: list[str] = Field(default_factory=list)
    protocol_availability: list[ProtocolAvailability] = Field(default_factory=list)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="finskillos-api",
        mode="READ_MODE",
        generated_at=datetime.now(tz=timezone.utc),
    )


@router.get("/system-status", response_model=SystemStatusResponse)
def system_status() -> SystemStatusResponse:
    """Return operational freshness without implying live market coverage.

    The v4.2 cockpit is still fixture-first for visual stability. This
    endpoint is the explicit operations contract: it reports whether the
    API can see the DB, which stored datasets have timestamps, and which
    System Ops protocols can run against the current environment.
    """

    generated_at = datetime.now(tz=timezone.utc)
    unavailable_protocols = _protocol_availability("UNAVAILABLE", "database unavailable")

    try:
        from finskillos.config import get_settings
        from finskillos.db.models.event import Event
        from finskillos.db.models.indicator import IndicatorSnapshot
        from finskillos.db.models.market import MarketBar
        from finskillos.db.models.news import NewsArticle
        from finskillos.db.models.portfolio import PortfolioSnapshot
        from finskillos.db.models.regime import MarketRegime

        engine = _status_engine(get_settings().database_url)
        session_factory = sessionmaker(
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
        )
        with session_factory() as session:
            session.execute(text("SELECT 1"))
            latest_portfolio = _max_iso(session, PortfolioSnapshot.snapshot_date)
            latest_market = _max_iso(session, MarketBar.bar_time)
            latest_indicator = _max_iso(session, IndicatorSnapshot.snapshot_time)
            latest_regime = _max_iso(session, MarketRegime.snapshot_time)
            latest_news = _max_iso(session, NewsArticle.published_at)
            latest_event = _max_iso(session, Event.updated_at)
    except Exception:
        return SystemStatusResponse(
            generated_at=generated_at,
            mode="READ_MODE",
            api_status="LIVE",
            db_status="MISSING",
            source="fixture",
            data_completeness="missing",
            stale_flags=["db_unavailable", "live_snapshots_unavailable"],
            protocol_availability=unavailable_protocols,
        )

    freshness = {
        "latest_portfolio_snapshot_at": latest_portfolio,
        "latest_market_bar_at": latest_market,
        "latest_indicator_at": latest_indicator,
        "latest_regime_at": latest_regime,
        "latest_news_at": latest_news,
        "latest_event_at": latest_event,
    }
    stale_flags = [
        f"{field.removeprefix('latest_').removesuffix('_at')}_missing"
        for field, value in freshness.items()
        if value is None
    ]

    return SystemStatusResponse(
        generated_at=generated_at,
        mode="READ_MODE",
        api_status="LIVE",
        db_status="LIVE",
        source="live",
        data_completeness="complete" if not stale_flags else "partial",
        latest_portfolio_snapshot_at=latest_portfolio,
        latest_market_bar_at=latest_market,
        latest_indicator_at=latest_indicator,
        latest_regime_at=latest_regime,
        latest_news_at=latest_news,
        latest_event_at=latest_event,
        stale_flags=stale_flags,
        protocol_availability=_protocol_availability(
            "AVAILABLE",
            "database reachable; protocol remains idempotent and descriptive",
        ),
    )


def _status_engine(database_url: str) -> Engine:
    if database_url.startswith("postgresql"):
        return create_engine(
            database_url,
            future=True,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 1},
        )
    return create_engine(database_url, future=True, pool_pre_ping=True)


def _max_iso(session: Session, column) -> str | None:
    value = session.execute(select(func.max(column))).scalar_one_or_none()
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _protocol_availability(
    status: Literal["AVAILABLE", "NOOP", "UNAVAILABLE"],
    detail: str,
) -> list[ProtocolAvailability]:
    return [
        ProtocolAvailability(key=key, status=status, detail=detail)
        for key in (
            "seed_sample_account",
            "seed_sample_events",
            "recompute_regime",
            "run_risk_guards",
        )
    ]


__all__ = ["router"]
