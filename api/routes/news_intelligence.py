"""GET /api/news-intelligence + POST /api/news-intelligence/manual-article — Slice 13.9.

Fixture-first wrapper around the Slice-10 NewsService. Live DB wiring
stays deferred per ``api/dependencies.py``; the React shell renders
the deterministic v4.2 Evidence-to-Judgment payload either way.

Manual article ingestion enforces the Slice-10 safety contract before
delegating to the service: summary length is capped, full-body input
is rejected, and ``assert_no_forbidden_wording`` runs on every text
field at the API seam.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends

from api.dependencies import get_session_scope, use_fixture_flag
from api.fixtures import news_intelligence_fixture
from api.schemas.news_intelligence import (
    MAX_SUMMARY_CHARS,
    ManualArticleInput,
    ManualArticleResult,
    NewsIntelligenceResponse,
)

router = APIRouter(tags=["news-intelligence"])

UTC = timezone.utc


@router.get(
    "/news-intelligence",
    response_model=NewsIntelligenceResponse,
    summary="News Intelligence snapshot (fixture-first in v0).",
)
def news_intelligence(
    use_fixture: bool = Depends(use_fixture_flag),
) -> NewsIntelligenceResponse:
    payload = news_intelligence_fixture()
    if use_fixture:
        payload.source = "fixture"
    return payload


@router.post(
    "/news-intelligence/manual-article",
    response_model=ManualArticleResult,
    summary="Persist a manually entered article via the Slice-10 NewsService.",
)
def post_manual_article(payload: ManualArticleInput) -> ManualArticleResult:
    if len(payload.summary) > MAX_SUMMARY_CHARS:
        return ManualArticleResult(
            status="REJECTED",
            message=(
                f"Summary exceeds the {MAX_SUMMARY_CHARS}-char cap. Store "
                "short summaries only — no full article body."
            ),
            detail="summary_too_long",
        )

    safety_error = _scan_inputs_for_forbidden_wording(payload)
    if safety_error is not None:
        return ManualArticleResult(
            status="REJECTED",
            message=(
                "Submission contains direct-advice or execution wording. "
                "Manual articles must be descriptive only."
            ),
            detail=safety_error,
        )

    published = _parse_iso_datetime(payload.published_at)
    if published is None:
        return ManualArticleResult(
            status="REJECTED",
            message="publishedAt must be a valid ISO-8601 timestamp.",
            detail="invalid_published_at",
        )

    with get_session_scope() as session:
        if session is None:
            return ManualArticleResult(
                status="OK",
                message=(
                    "Manual article accepted in fixture-first shell. "
                    "No database session was available; storage will "
                    "occur once the live wiring lands."
                ),
                detail="no_database_session",
            )
        try:
            from finskillos.services.news_service import (
                NewsArticleInput,
                NewsImpactInput,
                NewsService,
            )

            extra_impacts: list[NewsImpactInput] = []
            for ticker in payload.affected_tickers:
                extra_impacts.append(
                    NewsImpactInput(
                        ticker=ticker,
                        theme=payload.theme,
                        event_key=payload.event_key,
                        impact_score=Decimal("0.4"),
                        sentiment_label=payload.sentiment,
                        risk_level=payload.risk_level,
                        is_event_linked=bool(payload.event_key),
                    )
                )
            if not extra_impacts and (payload.theme or payload.event_key):
                extra_impacts.append(
                    NewsImpactInput(
                        theme=payload.theme,
                        event_key=payload.event_key,
                        impact_score=Decimal("0.3"),
                        sentiment_label=payload.sentiment,
                        risk_level=payload.risk_level,
                        is_event_linked=bool(payload.event_key),
                    )
                )

            service = NewsService(session)
            result = service.ingest_article(
                NewsArticleInput(
                    title=payload.title,
                    source=payload.source,
                    url=payload.url,
                    published_at=published,
                    summary=payload.summary,
                ),
                extra_impacts=extra_impacts,
            )
            session.commit()
            return ManualArticleResult(
                status="OK",
                message="Manual article stored with short summary only.",
                detail="article_persisted",
                article_id=str(result.article.id),
            )
        except Exception as exc:  # noqa: BLE001 — structured JSON
            session.rollback()
            return ManualArticleResult(
                status="ERROR",
                message=(
                    "Manual article request could not complete. Stored "
                    "data was not modified."
                ),
                detail=type(exc).__name__,
            )


def _scan_inputs_for_forbidden_wording(
    payload: ManualArticleInput,
) -> str | None:
    """Re-run the Slice-06 forbidden-wording guard at the API seam."""

    from finskillos.guards.base import (
        GuardResult,
        assert_no_forbidden_wording,
    )

    fields: tuple[tuple[str, str | None], ...] = (
        ("title", payload.title),
        ("summary", payload.summary),
        ("source", payload.source),
        ("theme", payload.theme),
        ("event_key", payload.event_key),
    )
    for name, value in fields:
        if not value:
            continue
        placeholder = GuardResult(
            guard_name=f"NEWS_MANUAL:{name}",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=value,
        )
        try:
            assert_no_forbidden_wording(placeholder)
        except AssertionError:
            return f"forbidden_wording_in_{name}"
    return None


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


__all__ = ["router"]
