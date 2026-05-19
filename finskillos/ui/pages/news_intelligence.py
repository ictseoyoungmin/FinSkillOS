"""News Intelligence — Slice 10 page.

Renders the read-only News Intelligence screen: holdings-relevant
news, latest news, event-linked news, and a small impact map (affected
tickers + sectors). A collapsible expander exposes a manual-article
insert form so a single-user MVP can seed the news store without an
adapter.

Streamlit is imported lazily inside ``render`` / per-section helpers
so the module stays importable in non-Streamlit test contexts.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.services.news_service import (
    NewsArticleInput,
    NewsImpactInput,
    NewsService,
)
from finskillos.ui.view_models import (
    NewsArticleVM,
    NewsIntelligenceViewModel,
    assert_news_intelligence_view_model_is_safe,
    build_news_intelligence_view_model,
)

UTC = timezone.utc

_MANUAL_FORM_KEY = "news_intelligence_manual_form"


def render(session: Session) -> None:
    import streamlit as st

    st.markdown("## News Intelligence")
    st.caption(
        "저장된 뉴스 기사 + 영향도 매핑을 모아서 서술적으로 점검합니다. "
        "원문 전체가 아닌 짧은 요약과 출처 링크만 표시하며, 매수 / 매도 "
        "지시가 아닌 상태 관찰용입니다."
    )

    vm = build_news_intelligence_view_model(session)
    assert_news_intelligence_view_model_is_safe(vm)

    if vm.setup_hint:
        st.info(vm.setup_hint)

    _render_summary_chips(vm)
    _render_holdings_relevant(vm)
    _render_latest_news(vm)
    _render_event_linked(vm)
    _render_impact_map(vm)
    _render_manual_insert(session)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _render_summary_chips(vm: NewsIntelligenceViewModel) -> None:
    import streamlit as st

    cols = st.columns(3)
    cols[0].metric("Latest articles", len(vm.latest_news))
    cols[1].metric("Holdings-relevant", len(vm.holdings_relevant))
    cols[2].metric("Event-linked", len(vm.event_linked))


# ---------------------------------------------------------------------------
# Article sections
# ---------------------------------------------------------------------------


def _render_holdings_relevant(vm: NewsIntelligenceViewModel) -> None:
    import streamlit as st

    st.markdown("### Holdings-relevant News")
    if not vm.holdings_relevant:
        st.caption(
            "현재 계좌 보유 종목과 연결된 뉴스가 없습니다. 종목/섹터/테마 "
            "매핑이 등록되면 이 영역에 표시됩니다."
        )
        return
    _render_article_table(vm.holdings_relevant)


def _render_latest_news(vm: NewsIntelligenceViewModel) -> None:
    import streamlit as st

    st.markdown("### Latest News")
    if not vm.latest_news:
        st.caption("저장된 뉴스 기사가 없습니다.")
        return
    _render_article_table(vm.latest_news)


def _render_event_linked(vm: NewsIntelligenceViewModel) -> None:
    import streamlit as st

    st.markdown("### Event-linked News")
    if not vm.event_linked:
        st.caption("이벤트(어닝/실적/매크로/우주 발사 등)에 연결된 뉴스가 없습니다.")
        return
    _render_article_table(vm.event_linked)


def _render_article_table(articles: tuple[NewsArticleVM, ...]) -> None:
    import streamlit as st

    rows = [
        {
            "Published": article.published_at.strftime("%Y-%m-%d %H:%M %Z"),
            "Source": article.source,
            "Title": article.title,
            "Tickers": _join_unique(impact.ticker for impact in article.impacts),
            "Sectors": _join_unique(impact.sector for impact in article.impacts),
            "Themes": _join_unique(impact.theme for impact in article.impacts),
            "Sentiment": _join_unique(
                impact.sentiment_label for impact in article.impacts
            ),
            "Event": "✓" if article.has_event_linked_impact() else "—",
        }
        for article in articles
    ]
    st.dataframe(rows, hide_index=True, width="stretch")

    with st.expander("기사별 요약 + 출처 링크"):
        for article in articles:
            st.markdown(f"**{article.title}**")
            st.caption(
                f"{article.source} · "
                f"{article.published_at.strftime('%Y-%m-%d %H:%M %Z')}"
            )
            st.write(article.summary)
            st.markdown(f"[원문 링크]({article.url})")
            st.divider()


# ---------------------------------------------------------------------------
# Impact map
# ---------------------------------------------------------------------------


def _render_impact_map(vm: NewsIntelligenceViewModel) -> None:
    import streamlit as st

    st.markdown("### Impact Map")
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Affected Tickers**")
        if vm.affected_tickers:
            st.write(", ".join(vm.affected_tickers))
        else:
            st.caption("해당되는 종목 영향도가 없습니다.")
    with cols[1]:
        st.markdown("**Affected Sectors / Themes**")
        if vm.affected_sectors:
            st.write(", ".join(vm.affected_sectors))
        else:
            st.caption("해당되는 섹터 영향도가 없습니다.")


# ---------------------------------------------------------------------------
# Manual entry form
# ---------------------------------------------------------------------------


def _render_manual_insert(session: Session) -> None:
    import streamlit as st

    st.markdown("### Manual Article Entry")
    st.caption(
        "원문 전체가 아닌 제목 + 짧은 요약 + 출처 URL만 입력하세요. "
        "summary는 자동으로 500자 이내로 잘립니다."
    )

    with st.expander("새 기사 직접 등록"):
        with st.form(_MANUAL_FORM_KEY, clear_on_submit=True):
            title = st.text_input("Title")
            source = st.text_input("Source", value="manual")
            url = st.text_input("URL")
            published_date = st.date_input(
                "Published date",
                value=datetime.now(tz=UTC).date(),
            )
            summary = st.text_area("Short summary", max_chars=500)
            ticker = st.text_input("Linked ticker (선택)", value="")
            sector = st.text_input("Linked sector (선택)", value="")
            theme = st.text_input("Linked theme (선택)", value="")
            submit = st.form_submit_button("Save article")

        if submit:
            if not (title and url and summary):
                st.error("Title / URL / summary는 필수입니다.")
                return
            extra = ()
            if ticker.strip() or sector.strip() or theme.strip():
                extra = (
                    NewsImpactInput(
                        ticker=ticker.strip().upper() or None,
                        sector=sector.strip() or None,
                        theme=theme.strip() or None,
                        impact_score=Decimal("0.3"),
                    ),
                )
            NewsService(session).ingest_article(
                NewsArticleInput(
                    title=title.strip(),
                    source=source.strip() or "manual",
                    url=url.strip(),
                    published_at=datetime.combine(
                        published_date, time(), tzinfo=UTC
                    ),
                    summary=summary.strip(),
                ),
                extra_impacts=extra,
            )
            st.success(
                "기사가 저장되었습니다. 페이지를 새로고침하면 목록에 반영됩니다."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _join_unique(items) -> str:  # type: ignore[no-untyped-def]
    seen: list[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.append(item)
    return ", ".join(seen) if seen else "—"
