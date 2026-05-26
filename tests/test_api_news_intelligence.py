"""Slice 13.9 — FastAPI /api/news-intelligence contract tests.

Verifies:

* GET response shape (judgment header, drivers, conflicts, evidence
  lists, impact map, interpretation, watchpoints, manual-entry rules).
* camelCase field names for the React client.
* POST /api/news-intelligence/manual-article rejects:
    - summaries longer than MAX_SUMMARY_CHARS,
    - forbidden execution / direct-advice wording,
    - invalid ISO timestamps.
* No execution / order / buy / sell concepts leak into the JSON.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.fixtures import FIXTURE_TIMESTAMP
from api.main import create_app
from finskillos.config import reset_settings_cache
from finskillos.db.base import Base
from finskillos.services.news_service import NewsArticleInput, NewsService

_FORBIDDEN_WORDS = (
    "buy",
    "sell",
    "execute",
    "place order",
    "trade now",
    "지금 사라",
    "지금 팔아라",
    "매수",
    "매도",
)


def _client() -> TestClient:
    return TestClient(create_app())


def test_news_intelligence_returns_full_payload() -> None:
    response = _client().get("/api/news-intelligence")
    assert response.status_code == 200
    body = response.json()
    expected = {
        "generatedAt",
        "systemStatus",
        "judgment",
        "drivers",
        "conflicts",
        "holdingsRelevant",
        "eventLinked",
        "latestNews",
        "impactMap",
        "integratedInterpretation",
        "watchpoints",
        "manualEntryRules",
        "safetyCaption",
        "source",
    }
    assert expected.issubset(body.keys())
    assert body["generatedAt"] == FIXTURE_TIMESTAMP


def test_news_intelligence_snapshot_exposes_v42_contract() -> None:
    body = _client().get("/api/news-intelligence").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["impactMap"]
    assert body["manualEntryRules"]["maxSummaryChars"] == 500
    assert "Descriptive narrative view only" in body["safetyCaption"]


def test_news_intelligence_judgment_header_fields_are_present() -> None:
    body = _client().get("/api/news-intelligence").json()
    judgment = body["judgment"]
    for key in (
        "headline",
        "confidence",
        "dominantTheme",
        "portfolioRelevance",
        "eventLinkage",
        "sentimentTone",
        "riskTone",
    ):
        assert key in judgment, judgment


def test_news_intelligence_articles_only_carry_short_summaries() -> None:
    body = _client().get("/api/news-intelligence").json()
    for article in body["latestNews"]:
        assert len(article["summary"]) <= 500, article


def test_news_intelligence_manual_entry_rules_use_safe_caps() -> None:
    body = _client().get("/api/news-intelligence").json()
    rules = body["manualEntryRules"]
    assert rules["maxSummaryChars"] == 500
    assert rules["forbidFullBody"] is True
    assert "no full article body" in rules["disclaimer"].lower()


def test_news_intelligence_payload_contains_no_forbidden_wording() -> None:
    raw = json.dumps(_client().get("/api/news-intelligence").json()).lower()
    # The Slice-13.9 payload describes "sell-the-news" only via the
    # event-radar post_event_note (not part of /news-intelligence), so
    # bare 'sell' tokens must not appear here.
    for forbidden in _FORBIDDEN_WORDS:
        assert forbidden not in raw, (
            f"News Intelligence payload leaks forbidden wording: {forbidden!r}"
        )


def test_manual_article_rejects_over_cap_summary() -> None:
    response = _client().post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "Probe",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "x" * 700,
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "summary_too_long"


def test_manual_article_rejects_over_cap_summary_with_structured_response() -> None:
    response = _client().post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "Probe",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "x" * 700,
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "summary_too_long"


def test_manual_article_accepts_summary_at_cap() -> None:
    response = _client().post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "Probe",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "x" * 500,
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"OK", "ERROR"}
    # Fixture-first session returns OK with no_database_session detail.


def test_manual_article_rejects_forbidden_wording() -> None:
    response = _client().post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "지금 사라",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "Descriptive summary.",
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert "forbidden_wording" in body["detail"]


def test_manual_article_rejects_invalid_published_at() -> None:
    response = _client().post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "Probe",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "not-a-timestamp",
            "summary": "Descriptive summary.",
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "invalid_published_at"


def test_use_fixture_header_is_accepted_on_news_intelligence() -> None:
    response = _client().get(
        "/api/news-intelligence", headers={"X-FSO-Use-Fixture": "1"}
    )
    assert response.status_code == 200
    assert response.json()["source"] == "fixture"


def test_news_intelligence_get_reads_stored_db_news(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "finskillos.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        NewsService(session).ingest_article(
            NewsArticleInput(
                title="AAPL data center update",
                source="RSS Desk",
                url="https://news.example.com/aapl-data-center",
                published_at=_dt("2026-05-26T12:30:00+00:00"),
                summary="Apple data center investment remained in focus.",
            )
        )
        session.commit()

    monkeypatch.setenv("FINSKILLOS_SKIP_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", database_url)
    reset_settings_cache()

    try:
        response = _client().get("/api/news-intelligence")
        assert response.status_code == 200
        body = response.json()

        assert body["source"] == "live"
        assert body["latestNews"][0]["title"] == "AAPL data center update"
        assert body["latestNews"][0]["source"] == "RSS Desk"
        assert body["latestNews"][0]["publishedAt"].startswith("2026-05-26T12:30:00")
        assert (
            body["judgment"]["portfolioRelevance"]
            == "0 current-holding matches; tracked tickers have stored news"
        )
        assert body["drivers"][1]["label"] == "Tracked ticker mentions"
        assert "not necessarily current holdings" in body["drivers"][1]["detail"]
        assert "streaming feed" in json.dumps(body).lower()
        assert "Reuters / Bloomberg / WSJ" not in json.dumps(body)
    finally:
        reset_settings_cache()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _dt(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)
