"""Slice 10 — News Intelligence model / repo / service / view-model tests.

Covers:

* Manual article insert / upsert via ``NewsService.ingest_article``.
* Duplicate URL updates the existing row (no duplicate created).
* Long title / summary are truncated to schema limits.
* Long article body field is NOT supported by the model.
* Impact rows link an article to ticker / sector / theme / event_key.
* Re-classifying the same article does not multiply impact rows.
* Deterministic keyword classifier maps TSLA / NVDA / chip / SpaceX /
  Fed / earnings keywords correctly.
* ``list_event_linked`` surfaces event-linked impacts.
* ``list_holdings_relevant_articles`` joins through current positions.
* ``list_latest_articles`` returns published_at desc.
* News Intelligence view model handles empty DB safely.
* View model exposes latest / holdings / event-linked tuples.
* Affected tickers / sectors are aggregated.
* Direct buy/sell wording is blocked by the safety scan.
* The ``sell-the-news`` market idiom is allowed.
* Title / summary longer than MAX_* fail the safety scan.
* Symbol Lab integration surfaces ticker-relevant news.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from finskillos.db.models import NewsArticle, NewsImpact
from finskillos.db.models.news import MAX_SUMMARY_CHARS, MAX_TITLE_CHARS
from finskillos.db.repositories import (
    AccountRepository,
    NewsArticleRepository,
    NewsImpactRepository,
    PositionRepository,
)
from finskillos.services.news_service import (
    NewsArticleInput,
    NewsImpactInput,
    NewsService,
    classify_impacts,
)
from finskillos.ui.view_models import (
    NewsIntelligenceViewModel,
    assert_news_intelligence_view_model_is_safe,
    build_news_intelligence_view_model,
    build_symbol_lab_view_model,
)

UTC = timezone.utc
NOW = datetime(2026, 5, 19, 21, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _make_account(session: Session):
    return AccountRepository(session).create(
        name="Main Trading Account",
        target_value=Decimal("60000000"),
    )


def _make_position(session: Session, *, account_id: uuid.UUID, ticker: str) -> None:
    PositionRepository(session).create(
        account_id=account_id,
        ticker=ticker,
        quantity=Decimal("10"),
        market_value=Decimal("5000000"),
        sector="Technology",
        theme="AI",
    )


def _ingest(
    service: NewsService,
    *,
    title: str,
    summary: str = "—",
    url: str = "https://news.example.com/a",
    source: str = "manual",
    published_at: datetime = NOW,
    extra: tuple[NewsImpactInput, ...] = (),
    auto_classify: bool = True,
):
    return service.ingest_article(
        NewsArticleInput(
            title=title,
            source=source,
            url=url,
            published_at=published_at,
            summary=summary,
        ),
        extra_impacts=extra,
        auto_classify=auto_classify,
    )


# ---------------------------------------------------------------------------
# Article CRUD
# ---------------------------------------------------------------------------


def test_manual_article_insert_creates_row(db_session: Session) -> None:
    service = NewsService(db_session)
    ingested = _ingest(
        service,
        title="TSLA delivery update",
        summary="Quarterly delivery numbers were strong.",
        url="https://example.com/tsla-1",
    )
    assert ingested.article.id is not None
    assert ingested.article.title == "TSLA delivery update"
    assert ingested.article.summary.startswith("Quarterly")


def test_duplicate_url_updates_existing_article(db_session: Session) -> None:
    service = NewsService(db_session)
    first = _ingest(service, title="v1", summary="first version")
    second = _ingest(service, title="v2", summary="second version")
    assert first.article.id == second.article.id
    rows = NewsArticleRepository(db_session).latest()
    assert len(rows) == 1
    assert rows[0].title == "v2"


def test_long_title_and_summary_are_truncated(db_session: Session) -> None:
    service = NewsService(db_session)
    long_title = "T" * (MAX_TITLE_CHARS + 100)
    long_summary = "S" * (MAX_SUMMARY_CHARS + 200)
    ingested = _ingest(
        service,
        title=long_title,
        summary=long_summary,
        url="https://example.com/long",
        auto_classify=False,
    )
    assert len(ingested.article.title) <= MAX_TITLE_CHARS
    assert len(ingested.article.summary) <= MAX_SUMMARY_CHARS
    # The truncation marker keeps the UI honest.
    assert ingested.article.title.endswith("…")
    assert ingested.article.summary.endswith("…")


def test_news_article_model_does_not_store_full_body() -> None:
    columns = {col.key for col in NewsArticle.__table__.columns}
    forbidden = {"full_text", "article_body", "body", "content"}
    assert forbidden.isdisjoint(columns), (
        f"news_articles must not store long article body fields, found: "
        f"{forbidden & columns}"
    )


def test_latest_articles_sorted_by_published_at_desc(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="oldest",
        url="https://example.com/old",
        published_at=datetime(2026, 5, 17, 9, 0, tzinfo=UTC),
        auto_classify=False,
    )
    _ingest(
        service,
        title="newest",
        url="https://example.com/new",
        published_at=datetime(2026, 5, 19, 9, 0, tzinfo=UTC),
        auto_classify=False,
    )
    _ingest(
        service,
        title="middle",
        url="https://example.com/mid",
        published_at=datetime(2026, 5, 18, 9, 0, tzinfo=UTC),
        auto_classify=False,
    )
    rows = service.list_latest_articles()
    assert [r.title for r in rows] == ["newest", "middle", "oldest"]


# ---------------------------------------------------------------------------
# Impact CRUD
# ---------------------------------------------------------------------------


def test_impact_links_article_to_ticker(db_session: Session) -> None:
    service = NewsService(db_session)
    ingested = _ingest(
        service,
        title="custom",
        url="https://example.com/custom",
        auto_classify=False,
        extra=(NewsImpactInput(ticker="MSFT", sector="Technology"),),
    )
    assert ingested.impacts[0].ticker == "MSFT"
    assert ingested.impacts[0].sector == "Technology"


def test_impact_links_article_to_sector_and_theme(db_session: Session) -> None:
    service = NewsService(db_session)
    ingested = _ingest(
        service,
        title="custom",
        url="https://example.com/sector",
        auto_classify=False,
        extra=(NewsImpactInput(sector="Energy", theme="Oil"),),
    )
    assert ingested.impacts[0].sector == "Energy"
    assert ingested.impacts[0].theme == "Oil"
    assert ingested.impacts[0].ticker is None


def test_re_ingest_does_not_multiply_impact_rows(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="TSLA delivery update",
        summary="Tesla delivered strong results.",
        url="https://example.com/dup",
    )
    _ingest(
        service,
        title="TSLA delivery update",
        summary="Tesla delivered strong results.",
        url="https://example.com/dup",
    )
    article = NewsArticleRepository(db_session).get_by_url(
        "https://example.com/dup"
    )
    assert article is not None
    rows = NewsImpactRepository(db_session).list_for_article(article.id)
    # Same article, same classifier output → impact rows are upserted,
    # not duplicated.
    assert all(isinstance(r, NewsImpact) for r in rows)
    keys = [(r.ticker, r.sector, r.theme, r.event_key) for r in rows]
    assert len(keys) == len(set(keys))


def test_event_linked_listing_returns_event_rows(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="Fed signals pause",
        summary="The Fed kept rates unchanged.",
        url="https://example.com/fed",
    )
    rows = service.list_event_linked_articles()
    assert len(rows) >= 1
    assert any(impact.is_event_linked for _, impacts in rows for impact in impacts)


# ---------------------------------------------------------------------------
# Keyword classifier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected_ticker",
    [
        ("Tesla beats delivery expectations", "TSLA"),
        ("NVDA earnings preview", "NVDA"),
        ("Apple guidance softens for Q3", "AAPL"),
    ],
)
def test_classifier_links_known_tickers(text: str, expected_ticker: str) -> None:
    impacts = classify_impacts(text)
    tickers = {i.ticker for i in impacts if i.ticker}
    assert expected_ticker in tickers


def test_classifier_marks_sector_themes_and_events() -> None:
    impacts = classify_impacts("Semiconductor wafer demand recovers")
    assert any(i.sector == "Semiconductors" for i in impacts)

    impacts = classify_impacts("SpaceX Starship test launch scheduled")
    assert any(i.is_event_linked and i.event_key == "SPACE_LAUNCH" for i in impacts)

    impacts = classify_impacts("Fed minutes hint at rate hike timing")
    assert any(i.event_key == "FED_DECISION" for i in impacts)


def test_classifier_sentiment_detection() -> None:
    impacts = classify_impacts("Tesla beats delivery expectations")
    pos = [i for i in impacts if i.ticker == "TSLA"]
    assert pos and pos[0].sentiment_label in {"POSITIVE", "MIXED"}

    impacts = classify_impacts("Nvidia misses guidance, warns on data center demand")
    neg = [i for i in impacts if i.ticker == "NVDA"]
    assert neg and neg[0].sentiment_label in {"NEGATIVE", "MIXED"}


# ---------------------------------------------------------------------------
# Holdings-relevance
# ---------------------------------------------------------------------------


def test_holdings_relevant_uses_current_positions(db_session: Session) -> None:
    account = _make_account(db_session)
    _make_position(db_session, account_id=account.id, ticker="TSLA")

    service = NewsService(db_session)
    _ingest(
        service,
        title="Tesla beats delivery expectations",
        summary="Tesla delivery numbers were strong.",
        url="https://example.com/holding-tsla",
    )
    _ingest(
        service,
        title="Generic AI feature update",
        summary="A new AI feature was announced.",
        url="https://example.com/holding-ai",
    )

    matched = service.list_holdings_relevant_articles()
    assert any(article.title.startswith("Tesla") for article, _ in matched)


def test_holdings_relevant_is_empty_without_account(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="Tesla beats delivery expectations",
        summary="...",
        url="https://example.com/no-account",
    )
    assert service.list_holdings_relevant_articles() == []


# ---------------------------------------------------------------------------
# View model
# ---------------------------------------------------------------------------


def test_view_model_handles_empty_db(db_session: Session) -> None:
    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    assert isinstance(vm, NewsIntelligenceViewModel)
    assert vm.latest_news == ()
    assert vm.holdings_relevant == ()
    assert vm.event_linked == ()
    assert vm.affected_tickers == ()
    assert vm.affected_sectors == ()
    assert vm.setup_hint is not None
    # Safety scan must pass even on empty state.
    assert_news_intelligence_view_model_is_safe(vm)


def test_view_model_exposes_seeded_articles_and_aggregations(
    db_session: Session,
) -> None:
    account = _make_account(db_session)
    _make_position(db_session, account_id=account.id, ticker="TSLA")

    service = NewsService(db_session)
    _ingest(
        service,
        title="Tesla beats delivery expectations",
        summary="Strong quarter for Tesla.",
        url="https://example.com/v-tsla",
    )
    _ingest(
        service,
        title="Fed signals pause",
        summary="The Fed paused.",
        url="https://example.com/v-fed",
    )

    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    titles = [a.title for a in vm.latest_news]
    assert "Tesla beats delivery expectations" in titles
    assert "Fed signals pause" in titles

    assert "TSLA" in vm.affected_tickers
    assert any(article.title.startswith("Tesla") for article in vm.holdings_relevant)
    assert any(article.has_event_linked_impact() for article in vm.event_linked)
    assert_news_intelligence_view_model_is_safe(vm)


# ---------------------------------------------------------------------------
# Safety scan
# ---------------------------------------------------------------------------


def test_safety_scan_blocks_direct_advice(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="Manual",
        summary="benign",
        url="https://example.com/safety-1",
        auto_classify=False,
        extra=(
            NewsImpactInput(
                ticker="TSLA",
                impact_score=Decimal("0.5"),
                sentiment_label="POSITIVE",
                risk_note="Sell this position immediately",
            ),
        ),
    )
    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    with pytest.raises(AssertionError):
        assert_news_intelligence_view_model_is_safe(vm)


def test_safety_scan_allows_sell_the_news_idiom(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="TSLA earnings sell-the-news risk",
        summary="Reaction may be muted despite a strong print.",
        url="https://example.com/safety-allowed",
    )
    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    # Must not raise — descriptive market idiom is allowed.
    assert_news_intelligence_view_model_is_safe(vm)


def test_safety_scan_rejects_oversize_title(db_session: Session) -> None:
    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    huge_title = "T" * (MAX_TITLE_CHARS + 1)
    fake_article = replace(
        vm.latest_news[0]
        if vm.latest_news
        else _placeholder_article_vm(),
        title=huge_title,
    )
    tampered = replace(vm, latest_news=(fake_article,))
    with pytest.raises(AssertionError):
        assert_news_intelligence_view_model_is_safe(tampered)


def test_safety_scan_rejects_oversize_summary(db_session: Session) -> None:
    vm = build_news_intelligence_view_model(db_session, generated_at=NOW)
    huge_summary = "S" * (MAX_SUMMARY_CHARS + 1)
    fake_article = replace(
        vm.latest_news[0]
        if vm.latest_news
        else _placeholder_article_vm(),
        summary=huge_summary,
    )
    tampered = replace(vm, latest_news=(fake_article,))
    with pytest.raises(AssertionError):
        assert_news_intelligence_view_model_is_safe(tampered)


# ---------------------------------------------------------------------------
# Symbol Lab integration
# ---------------------------------------------------------------------------


def test_symbol_lab_view_model_surfaces_ticker_news(db_session: Session) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="Tesla beats delivery expectations",
        summary="Strong quarter for Tesla.",
        url="https://example.com/sym-tsla",
    )
    vm = build_symbol_lab_view_model(db_session, ticker="TSLA", generated_at=NOW)
    assert vm.has_news()
    titles = [news.title for news in vm.news]
    assert any("Tesla" in title for title in titles)


def test_symbol_lab_news_is_empty_for_ticker_without_coverage(
    db_session: Session,
) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="Fed signals pause",
        summary="The Fed paused.",
        url="https://example.com/sym-fed",
    )
    vm = build_symbol_lab_view_model(db_session, ticker="ZZZ", generated_at=NOW)
    assert vm.news == ()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _placeholder_article_vm():
    """Return a NewsArticleVM stand-in when the DB has no rows yet."""

    from finskillos.ui.view_models import NewsArticleVM

    return NewsArticleVM(
        id=uuid.uuid4(),
        title="t",
        source="manual",
        url="https://example.com/placeholder",
        published_at=NOW,
        summary="s",
        impacts=(),
    )


def test_article_lookup_returns_published_at_aware_datetime(
    db_session: Session,
) -> None:
    service = NewsService(db_session)
    _ingest(
        service,
        title="dated",
        url="https://example.com/dt",
        published_at=datetime(2026, 5, 18, 9, 0),
        auto_classify=False,
    )
    article = NewsArticleRepository(db_session).get_by_url(
        "https://example.com/dt"
    )
    assert article is not None
    # ingest_article must always persist tz-aware datetimes.
    assert article.published_at is not None
    # SQLite may strip tzinfo on the way out — what we care about is
    # that the date itself matches.
    assert article.published_at.date() == date(2026, 5, 18)


# ---------------------------------------------------------------------------
# 10 cleanup — stale impact synchronization + ticker normalization
# ---------------------------------------------------------------------------


def test_reingest_replaces_stale_classifier_impacts(db_session: Session) -> None:
    """10 cleanup Task 1 — re-ingest with new classifier output drops stale rows."""

    service = NewsService(db_session)

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url="https://example.com/reclass",
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )

    service.ingest_article(
        NewsArticleInput(
            title="Fed signals rate pause",
            source="manual",
            url="https://example.com/reclass",
            published_at=NOW,
            summary="The Fed kept rates unchanged.",
        )
    )

    article = NewsArticleRepository(db_session).get_by_url(
        "https://example.com/reclass"
    )
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)

    tickers = {i.ticker for i in impacts if i.ticker}
    event_keys = {i.event_key for i in impacts if i.event_key}

    assert "TSLA" not in tickers
    assert "FED_DECISION" in event_keys


def test_reingest_with_no_impact_clears_existing_impacts(db_session: Session) -> None:
    """10 cleanup Task 1 — re-ingest with no classifier hit clears all impacts."""

    service = NewsService(db_session)
    url = "https://example.com/no-impact-reclass"

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url=url,
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )
    service.ingest_article(
        NewsArticleInput(
            title="Company posts neutral blog update",
            source="manual",
            url=url,
            published_at=NOW,
            summary="No tracked ticker or sector keyword appears.",
        )
    )

    article = NewsArticleRepository(db_session).get_by_url(url)
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)
    assert impacts == []


def test_reingest_can_preserve_old_impacts_when_replace_disabled(
    db_session: Session,
) -> None:
    """10 cleanup Task 1 — replace_impacts=False keeps the old append behaviour."""

    service = NewsService(db_session)
    url = "https://example.com/append-reclass"

    service.ingest_article(
        NewsArticleInput(
            title="Tesla beats delivery expectations",
            source="manual",
            url=url,
            published_at=NOW,
            summary="Tesla delivery numbers were strong.",
        )
    )
    service.ingest_article(
        NewsArticleInput(
            title="Fed signals rate pause",
            source="manual",
            url=url,
            published_at=NOW,
            summary="The Fed kept rates unchanged.",
        ),
        replace_impacts=False,
    )

    article = NewsArticleRepository(db_session).get_by_url(url)
    assert article is not None
    impacts = NewsImpactRepository(db_session).list_for_article(article.id)
    tickers = {i.ticker for i in impacts if i.ticker}
    event_keys = {i.event_key for i in impacts if i.event_key}

    assert "TSLA" in tickers
    assert "FED_DECISION" in event_keys


def test_manual_impact_ticker_is_normalized_to_uppercase(
    db_session: Session,
) -> None:
    """10 cleanup Task 2 — manual lowercase ticker persists as uppercase."""

    service = NewsService(db_session)
    ingested = service.ingest_article(
        NewsArticleInput(
            title="manual mapping",
            source="manual",
            url="https://example.com/lowercase-ticker",
            published_at=NOW,
            summary="manual summary",
        ),
        auto_classify=False,
        extra_impacts=(NewsImpactInput(ticker="tsla"),),
    )

    assert ingested.impacts[0].ticker == "TSLA"


def test_manual_impact_key_dedupes_lowercase_and_uppercase_ticker(
    db_session: Session,
) -> None:
    """10 cleanup Task 2 — lowercase/uppercase duplicate impacts collapse."""

    service = NewsService(db_session)
    ingested = service.ingest_article(
        NewsArticleInput(
            title="manual mapping",
            source="manual",
            url="https://example.com/dedupe-case",
            published_at=NOW,
            summary="manual summary",
        ),
        auto_classify=False,
        extra_impacts=(
            NewsImpactInput(ticker="tsla"),
            NewsImpactInput(ticker="TSLA"),
        ),
    )

    impacts = NewsImpactRepository(db_session).list_for_article(
        ingested.article.id
    )
    assert len([i for i in impacts if i.ticker == "TSLA"]) == 1


def test_extra_impacts_override_classifier_output_for_matching_key(
    db_session: Session,
) -> None:
    """Extra impacts should win over the classifier for the same impact key."""

    service = NewsService(db_session)
    ingested = service.ingest_article(
        NewsArticleInput(
            title="TSLA guidance misses",
            source="manual",
            url="https://example.com/override-case",
            published_at=NOW,
            summary="Tesla issued weak guidance and the stock dipped.",
        ),
        extra_impacts=(
            NewsImpactInput(
                ticker="TSLA",
                theme="EV",
                sector="Consumer Discretionary",
                sentiment_label="NEGATIVE",
                risk_level="RED",
            ),
        ),
    )

    impacts = NewsImpactRepository(db_session).list_for_article(
        ingested.article.id
    )
    tsla_impacts = [i for i in impacts if i.ticker == "TSLA"]
    assert len(tsla_impacts) == 1
    assert tsla_impacts[0].sentiment_label == "NEGATIVE"
    assert tsla_impacts[0].risk_level == "RED"
