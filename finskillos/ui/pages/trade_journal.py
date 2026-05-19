"""Trade Memory / Trade Journal — Slice 12 page.

Reflection-first journal page: recent entries table, performance
breakdowns (regime / sector / strategy), mistake tag frequency,
weekly review block (copyable markdown), and a manual entry form.

Streamlit is imported lazily inside ``render`` / per-section helpers
so the module stays importable in non-Streamlit test contexts. The
page intentionally exposes only reflection-style buttons (Add
journal entry, Save entry, Refresh review, Generate weekly review,
Export review) — never direct-execution wording.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from finskillos.services.trade_journal_service import (
    DEFAULT_MISTAKE_TAGS,
    SIDE_LONG,
    SLICE_12_SIDES,
    TradeJournalInput,
    TradeJournalService,
)
from finskillos.ui.view_models import (
    TradeEntryVM,
    TradeMemoryViewModel,
    assert_trade_memory_view_model_is_safe,
    build_trade_memory_view_model,
)

UTC = timezone.utc

_MANUAL_FORM_KEY = "trade_journal_manual_form"


def render(session: Session) -> None:
    import streamlit as st

    st.markdown("## Trade Memory · Trade Journal")
    st.caption(
        "성과를 점수로 보여주는 화면이 아니라 매매 과정의 결정 / 감정 / 실수 "
        "패턴을 되돌아보기 위한 화면입니다. 매수 / 매도 지시가 아닌 process "
        "review 용입니다."
    )

    vm = build_trade_memory_view_model(session)
    assert_trade_memory_view_model_is_safe(vm)

    if vm.setup_hint:
        st.info(vm.setup_hint)

    _render_summary_chips(vm)
    _render_recent_entries(vm)
    _render_performance_section(vm)
    _render_mistake_section(vm)
    _render_weekly_review(vm)
    _render_manual_entry(session)


# ---------------------------------------------------------------------------
# Summary chips
# ---------------------------------------------------------------------------


def _render_summary_chips(vm: TradeMemoryViewModel) -> None:
    import streamlit as st

    cols = st.columns(3)
    cols[0].metric("Recent entries", len(vm.recent_entries))
    cols[1].metric(
        "Regimes observed",
        len(vm.performance_by_regime),
    )
    cols[2].metric(
        "Mistake tags this week",
        len(vm.weekly_review.most_common_mistakes),
    )


# ---------------------------------------------------------------------------
# Recent entries
# ---------------------------------------------------------------------------


def _render_recent_entries(vm: TradeMemoryViewModel) -> None:
    import streamlit as st

    st.markdown("### Recent Entries")
    if not vm.recent_entries:
        st.caption(
            "아직 저장된 매매 / 관찰 기록이 없습니다. 'Add journal entry' "
            "폼으로 첫 엔트리를 등록하세요."
        )
        return

    rows = [
        {
            "Date": entry.trade_date.isoformat(),
            "Ticker": entry.ticker,
            "Side": entry.side,
            "Strategy": entry.strategy_type or "—",
            "Regime": entry.market_regime or "—",
            "Sector": entry.sector or "—",
            "Theme": entry.theme or "—",
            "Emotion": entry.emotion_state or "—",
            "P&L": _fmt_decimal(entry.result_pnl, places=2),
            "P&L %": _fmt_decimal(entry.result_pnl_pct, places=2),
            "R": _fmt_decimal(entry.r_multiple, places=2),
            "Mistakes": ", ".join(entry.mistake_tags) or "—",
        }
        for entry in vm.recent_entries
    ]
    st.dataframe(rows, hide_index=True, width="stretch")

    with st.expander("기록별 thesis / 메모"):
        for entry in vm.recent_entries:
            _render_entry_detail(entry)


def _render_entry_detail(entry: TradeEntryVM) -> None:
    import streamlit as st

    st.markdown(
        f"**{entry.trade_date.isoformat()} · {entry.ticker} · {entry.side}**"
    )
    if entry.thesis:
        st.markdown(f"- **Thesis**: {entry.thesis}")
    if entry.reason:
        st.markdown(f"- **Reason**: {entry.reason}")
    if entry.catalyst:
        st.markdown(f"- **Catalyst**: {entry.catalyst}")
    if entry.notes:
        st.markdown(f"- **Notes**: {entry.notes}")
    if entry.mistake_tags:
        st.markdown(f"- **Mistake tags**: {', '.join(entry.mistake_tags)}")
    st.divider()


# ---------------------------------------------------------------------------
# Performance buckets
# ---------------------------------------------------------------------------


def _render_performance_section(vm: TradeMemoryViewModel) -> None:
    import streamlit as st

    st.markdown("### Reflection Overview")

    cols = st.columns(3)
    with cols[0]:
        st.markdown("**Performance by regime**")
        _render_perf_table(vm.performance_by_regime, key_label="Regime")
    with cols[1]:
        st.markdown("**Performance by sector / theme**")
        _render_perf_table(
            vm.performance_by_sector_theme, key_label="Sector / Theme"
        )
    with cols[2]:
        st.markdown("**Performance by strategy type**")
        _render_perf_table(vm.performance_by_strategy, key_label="Strategy")


def _render_perf_table(buckets, *, key_label: str) -> None:  # type: ignore[no-untyped-def]
    import streamlit as st

    if not buckets:
        st.caption("표시할 데이터가 없습니다.")
        return
    rows = [
        {
            key_label: bucket.key,
            "Trades": bucket.trade_count,
            "Total P&L": _fmt_decimal(bucket.total_pnl, places=2),
            "Avg P&L": _fmt_decimal(bucket.avg_pnl, places=2),
            "Avg R": _fmt_decimal(bucket.avg_r_multiple, places=2),
            "Win rate": _fmt_pct(bucket.win_rate),
        }
        for bucket in buckets
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Mistake tags
# ---------------------------------------------------------------------------


def _render_mistake_section(vm: TradeMemoryViewModel) -> None:
    import streamlit as st

    st.markdown("### Mistake Tag Frequency")
    if not vm.mistake_frequency:
        st.caption("저장된 mistake 태그가 없습니다.")
        return
    rows = [
        {
            "Tag": item.tag,
            "Count": item.count,
            "Losing trades": item.losing_trade_count,
            "Avg P&L": _fmt_decimal(item.avg_pnl, places=2),
        }
        for item in vm.mistake_frequency
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Weekly review
# ---------------------------------------------------------------------------


def _render_weekly_review(vm: TradeMemoryViewModel) -> None:
    import streamlit as st

    st.markdown("### Weekly Review")
    review = vm.weekly_review
    cols = st.columns(3)
    cols[0].metric("Trades this week", review.trade_count)
    cols[1].metric(
        "Total P&L",
        _fmt_decimal(review.total_pnl, places=2),
    )
    cols[2].metric("Win rate", _fmt_pct(review.win_rate))

    if review.process_notes:
        st.markdown("**Process notes**")
        for note in review.process_notes:
            st.markdown(f"- {note}")
    else:
        st.caption("리뷰할 항목이 충분하지 않습니다.")

    st.markdown("**Export-ready markdown**")
    st.caption(
        "아래 텍스트 영역을 복사해 외부 일기/Notion 등에 붙여넣을 수 "
        "있습니다. 직접 매수/매도 지시 문구는 포함되어 있지 않습니다."
    )
    st.text_area(
        "Weekly review markdown",
        value=vm.weekly_review_markdown,
        height=220,
        label_visibility="collapsed",
    )


# ---------------------------------------------------------------------------
# Manual entry
# ---------------------------------------------------------------------------


def _render_manual_entry(session: Session) -> None:
    import streamlit as st

    st.markdown("### Add Journal Entry")
    st.caption(
        "기록은 매매 실행 명령이 아니라 회고 / 관찰 / 학습용입니다. "
        "Side 값으로 LONG / SHORT / WATCH / EXIT_REVIEW / OTHER 를 선택하세요."
    )

    with st.expander("새 매매 기록 직접 등록"):
        with st.form(_MANUAL_FORM_KEY, clear_on_submit=True):
            trade_date = st.date_input(
                "Trade date", value=datetime.now(tz=UTC).date()
            )
            ticker = st.text_input("Ticker")
            side = st.selectbox(
                "Side",
                SLICE_12_SIDES,
                index=SLICE_12_SIDES.index(SIDE_LONG),
            )
            strategy_type = st.text_input("Strategy type", value="swing")
            amount = st.text_input("Amount (KRW, 선택)", value="")
            reason = st.text_area("Reason (선택)")
            thesis = st.text_area("Thesis (선택)")
            catalyst = st.text_input("Catalyst (선택)")
            market_regime = st.text_input(
                "Market regime (선택, 비우면 최신 regime 자동 캡처)"
            )
            emotion_state = st.text_input("Emotion state (선택)")
            result_pnl = st.text_input("Result P&L (KRW, 선택)", value="")
            result_pnl_pct = st.text_input("Result P&L % (선택)", value="")
            r_multiple = st.text_input("R multiple (선택)", value="")
            mistake_tags = st.multiselect(
                "Mistake tags",
                list(DEFAULT_MISTAKE_TAGS),
                default=[],
            )
            notes = st.text_area("Notes (선택)")
            sector = st.text_input("Sector (선택)")
            theme = st.text_input("Theme (선택)")
            event_key = st.text_input("Event key (선택)")
            submit = st.form_submit_button("Save entry")

        if submit:
            if not ticker.strip():
                st.error("Ticker 는 필수입니다.")
                return
            try:
                entry = TradeJournalInput(
                    trade_date=trade_date,
                    ticker=ticker,
                    side=side,
                    strategy_type=strategy_type or None,
                    amount=_parse_decimal(amount),
                    reason=reason or None,
                    thesis=thesis or None,
                    catalyst=catalyst or None,
                    market_regime=market_regime or None,
                    emotion_state=emotion_state or None,
                    result_pnl=_parse_decimal(result_pnl),
                    result_pnl_pct=_parse_decimal(result_pnl_pct),
                    r_multiple=_parse_decimal(r_multiple),
                    mistake_tags=tuple(mistake_tags),
                    notes=notes or None,
                    sector=sector or None,
                    theme=theme or None,
                    event_key=event_key or None,
                )
                TradeJournalService(session).create_entry(entry)
            except (ValueError, LookupError) as exc:
                st.error(str(exc))
                return
            st.success(
                "엔트리가 저장되었습니다. 페이지를 새로고침하면 목록 / "
                "리뷰가 업데이트됩니다."
            )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"숫자가 아닌 값입니다: {raw!r}") from exc


def _fmt_decimal(value: Decimal | None, *, places: int = 2) -> str:
    if value is None:
        return "—"
    quant = Decimal(10) ** -places
    return f"{value.quantize(quant)}"


def _fmt_pct(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{(value * Decimal('100')).quantize(Decimal('0.1'))}%"


__all__ = ["render"]
