"""Event Radar / Catalyst Watch — Slice 11 page.

Renders the read-only Event Radar screen: upcoming events table,
high-risk events, holdings-linked events, event-linked news, and a
collapsible expander for manual event entry / sample seeding.

Streamlit is imported lazily inside ``render`` / per-section helpers
so the module stays importable in non-Streamlit test contexts.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.db.models.event import (
    ALL_DATE_STATUSES,
    ALL_EVENT_TYPES,
    DATE_STATUS_TENTATIVE,
    EVENT_TYPE_OTHER,
)
from finskillos.services.event_service import (
    EventInput,
    EventLinkInput,
    EventService,
)
from finskillos.ui.view_models import (
    EventRadarViewModel,
    EventRiskVM,
    assert_event_radar_view_model_is_safe,
    build_event_radar_view_model,
)

UTC = timezone.utc

_DATE_STATUS_LABEL: dict[str, str] = {
    "CONFIRMED": "확정",
    "WINDOW": "기간",
    "TENTATIVE": "잠정",
    "REPORTED": "보도",
    "SPECULATIVE": "추정",
    "UNKNOWN": "미상",
}

_RISK_LABEL_LABEL: dict[str, str] = {
    "LOW": "낮음",
    "MODERATE": "보통",
    "HIGH": "높음",
    "CRITICAL": "심각",
}

_MANUAL_FORM_KEY = "event_radar_manual_form"
_SEED_BUTTON_KEY = "event_radar_seed_button"


def render(session: Session) -> None:
    import streamlit as st

    st.markdown("## Catalyst Watch · Event Radar")
    st.caption(
        "다가오는 catalyst를 미리 관찰하기 위한 화면입니다. "
        "확정되지 않은 이벤트는 TENTATIVE / WINDOW / SPECULATIVE 등으로 표시되며, "
        "매수 / 매도 지시가 아닌 노출 / 준비 점검용입니다."
    )

    vm = build_event_radar_view_model(session)
    assert_event_radar_view_model_is_safe(vm)

    if vm.setup_hint:
        st.info(vm.setup_hint)

    _render_summary_chips(vm)
    _render_high_risk(vm)
    _render_holdings_linked(vm)
    _render_upcoming_table(vm)
    _render_event_detail_expander(vm)
    _render_manual_entry(session)


# ---------------------------------------------------------------------------
# Summary chips
# ---------------------------------------------------------------------------


def _render_summary_chips(vm: EventRadarViewModel) -> None:
    import streamlit as st

    cols = st.columns(3)
    cols[0].metric("Upcoming events", len(vm.upcoming))
    cols[1].metric("High / critical risk", len(vm.high_risk))
    cols[2].metric("Holdings-linked", len(vm.holdings_linked))


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def _render_high_risk(vm: EventRadarViewModel) -> None:
    import streamlit as st

    st.markdown("### High-Risk Events")
    if not vm.high_risk:
        st.caption("HIGH / CRITICAL 등급 이벤트가 없습니다.")
        return
    _render_event_table(vm.high_risk)


def _render_holdings_linked(vm: EventRadarViewModel) -> None:
    import streamlit as st

    st.markdown("### Holdings-linked Events")
    if not vm.holdings_linked:
        st.caption(
            "현재 계좌 보유 종목과 연결된 이벤트가 없습니다. 종목 / 테마 / "
            "이벤트 키 매핑이 등록되면 이 영역에 표시됩니다."
        )
        return
    _render_event_table(vm.holdings_linked)


def _render_upcoming_table(vm: EventRadarViewModel) -> None:
    import streamlit as st

    st.markdown("### Upcoming Events")
    if not vm.upcoming:
        st.caption("저장된 이벤트가 없습니다.")
        return
    _render_event_table(vm.upcoming)


def _render_event_table(events: tuple[EventRiskVM, ...]) -> None:
    import streamlit as st

    rows = [
        {
            "Start": event.start_date.isoformat(),
            "End": event.end_date.isoformat() if event.end_date else "—",
            "Status": _DATE_STATUS_LABEL.get(event.date_status, event.date_status),
            "Type": event.event_type,
            "Title": event.title,
            "Days": event.days_to_event if event.days_to_event is not None else "—",
            "Importance": _fmt_decimal(event.importance_score, places=2),
            "Risk score": _fmt_decimal(event.event_risk_score, places=2),
            "Risk label": _RISK_LABEL_LABEL.get(
                event.risk_label, event.risk_label
            ),
            "Tickers": ", ".join(event.affected_tickers) or "—",
            "Sectors": ", ".join(event.affected_sectors) or "—",
            "Themes": ", ".join(event.affected_themes) or "—",
        }
        for event in events
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def _render_event_detail_expander(vm: EventRadarViewModel) -> None:
    import streamlit as st

    if not vm.upcoming:
        return

    with st.expander("이벤트별 노트 / 영향도 / 관련 뉴스"):
        for event in vm.upcoming:
            status_label = _DATE_STATUS_LABEL.get(
                event.date_status, event.date_status
            )
            risk_label = _RISK_LABEL_LABEL.get(
                event.risk_label, event.risk_label
            )
            st.markdown(f"**{event.title}**")
            st.caption(
                f"{event.event_type} · {status_label} · "
                f"Risk {_fmt_decimal(event.event_risk_score, places=2)} "
                f"({risk_label})"
            )
            if event.description:
                st.write(event.description)
            st.markdown(f"- **Pre-event**: {event.pre_event_note}")
            st.markdown(f"- **Post-event**: {event.post_event_note}")
            if event.linked_news:
                st.markdown("**Event-linked news**")
                for news in event.linked_news:
                    st.markdown(
                        f"- [{news.title}]({news.url}) · {news.source} · "
                        f"{news.published_at.strftime('%Y-%m-%d %H:%M %Z')} · "
                        f"{news.sentiment_label}"
                    )
            else:
                st.caption("매칭되는 event-linked news가 없습니다.")
            st.divider()


# ---------------------------------------------------------------------------
# Manual entry / seed
# ---------------------------------------------------------------------------


def _render_manual_entry(session: Session) -> None:
    import streamlit as st

    st.markdown("### Manual Event Entry")
    st.caption(
        "확정되지 않은 이벤트는 TENTATIVE / WINDOW / SPECULATIVE 로 표시하세요. "
        "Slice 11 v0는 외부 이벤트 피드를 자동 수집하지 않습니다."
    )

    with st.expander("샘플 이벤트 시드"):
        st.caption(
            "재실행해도 중복 생성되지 않습니다. 잠정 / 추정 이벤트만 "
            "등록되며 CONFIRMED 로 입력되지 않습니다."
        )
        if st.button("샘플 이벤트 등록", key=_SEED_BUTTON_KEY):
            created = EventService(session).seed_sample_events(
                today=datetime.now(tz=UTC).date()
            )
            st.success(f"새 이벤트 {len(created)}건이 등록되었습니다.")

    with st.expander("새 이벤트 직접 등록"):
        with st.form(_MANUAL_FORM_KEY, clear_on_submit=True):
            title = st.text_input("Title")
            event_type = st.selectbox(
                "Event type",
                ALL_EVENT_TYPES,
                index=ALL_EVENT_TYPES.index(EVENT_TYPE_OTHER),
            )
            date_status = st.selectbox(
                "Date status",
                ALL_DATE_STATUSES,
                index=ALL_DATE_STATUSES.index(DATE_STATUS_TENTATIVE),
            )
            start = st.date_input(
                "Start date",
                value=datetime.now(tz=UTC).date(),
            )
            end = st.date_input(
                "End date (선택)",
                value=datetime.now(tz=UTC).date(),
            )
            include_end = st.checkbox("End date 사용", value=False)
            importance = st.number_input(
                "Importance (0.0 ~ 5.0)",
                min_value=0.0,
                max_value=5.0,
                value=1.0,
                step=0.5,
            )
            source = st.text_input("Source (선택)", value="manual")
            source_url = st.text_input("Source URL (선택)", value="")
            description = st.text_area("Description (선택)")
            ticker = st.text_input("Linked ticker (선택)", value="")
            sector = st.text_input("Linked sector (선택)", value="")
            theme = st.text_input("Linked theme (선택)", value="")
            event_key = st.text_input("Linked event_key (선택)", value="")
            submit = st.form_submit_button("Save event")

        if submit:
            if not title:
                st.error("Title 은 필수입니다.")
                return
            event_input = EventInput(
                title=title.strip(),
                event_type=event_type,
                date_status=date_status,
                start_date=start,
                end_date=end if include_end else None,
                source=source.strip() or "manual",
                source_url=source_url.strip() or None,
                description=description.strip() or None,
                importance_score=Decimal(str(importance)),
            )
            links = ()
            if (
                ticker.strip()
                or sector.strip()
                or theme.strip()
                or event_key.strip()
            ):
                links = (
                    EventLinkInput(
                        ticker=ticker.strip().upper() or None,
                        sector=sector.strip() or None,
                        theme=theme.strip() or None,
                        event_key=event_key.strip() or None,
                    ),
                )
            try:
                EventService(session).create_event(event_input, links=links)
            except ValueError as exc:
                st.error(str(exc))
                return
            st.success(
                "이벤트가 저장되었습니다. 페이지를 새로고침하면 목록에 반영됩니다."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_decimal(value: Decimal | None, *, places: int = 2) -> str:
    if value is None:
        return "—"
    quant = Decimal(10) ** -places
    return f"{value.quantize(quant)}"


__all__ = ["render"]


# Tell type checkers that ``date`` is intentionally re-exported for tests.
_ = date
