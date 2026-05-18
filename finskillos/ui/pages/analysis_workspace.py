"""Analysis Workspace — Slice 08 Index Lab page.

Renders the first usable Research Hub screen: a US-market index / ETF /
macro overview table backed by stored ``market_bars`` +
``indicator_snapshots`` (Slice 04) plus the latest ``MarketRegime`` row
(Slice 05). Streamlit is imported lazily inside ``render`` so the
module stays importable in non-Streamlit test contexts.

This page is read-only. Refresh / recalculation actions remain on
System Ops; the Analysis Workspace itself does not mutate the DB.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.view_models import (
    IndexInstrumentVM,
    IndexLabViewModel,
    assert_index_lab_view_model_is_safe,
    build_index_lab_view_model,
)
from finskillos.ui.view_models.index_lab_vm import (
    DATA_STATUS_MISSING,
    DATA_STATUS_OK,
    DATA_STATUS_PARTIAL,
)

_DATA_STATUS_LABEL: dict[str, str] = {
    DATA_STATUS_OK: "정상",
    DATA_STATUS_PARTIAL: "부분",
    DATA_STATUS_MISSING: "누락",
}


def render(session: Session) -> None:
    import streamlit as st

    vm = build_index_lab_view_model(session)
    assert_index_lab_view_model_is_safe(vm)

    st.markdown("## Analysis Workspace")
    st.caption(
        "Index Lab — 지수 / ETF / 매크로 프록시의 가격 + 지표 + Regime 컨텍스트를 "
        "서술적으로 점검합니다. 매수 / 매도 지시가 아닌 시장 상태 관찰용입니다."
    )

    if vm.setup_hint:
        st.warning(vm.setup_hint)

    _render_regime_context(vm)
    _render_universe_table(vm)
    _render_strongest_weakest(vm)
    _render_missing_data(vm)


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def _render_regime_context(vm: IndexLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Regime Context")
    cards.render_regime_card(vm.regime)


def _render_universe_table(vm: IndexLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Index / ETF Universe")
    if not vm.universe:
        st.info("표시할 종목이 없습니다.")
        return

    rows = [_row_to_dict(row) for row in vm.universe]
    st.dataframe(rows, width="stretch", hide_index=True)

    with st.expander("Watchpoints (서술적 관찰 노트)"):
        for row in vm.universe:
            if not row.watchpoints:
                continue
            st.markdown(f"**{row.ticker} · {row.label}**")
            for note in row.watchpoints:
                st.markdown(f"- {note}")


def _render_strongest_weakest(vm: IndexLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Tape Strength")
    left, right = st.columns(2)
    with left:
        st.markdown("**Strongest Tape**")
        _render_strength_panel(vm.strongest, empty_label="강세 후보가 없습니다.")
    with right:
        st.markdown("**Weakest Tape**")
        _render_strength_panel(vm.weakest, empty_label="약세 후보가 없습니다.")


def _render_strength_panel(
    rows: tuple[IndexInstrumentVM, ...],
    *,
    empty_label: str,
) -> None:
    import streamlit as st

    if not rows:
        st.caption(empty_label)
        return
    for row in rows:
        score_label = _format_score(row.relative_strength_score)
        trend_label = row.trend_state or "—"
        st.metric(
            label=f"{row.ticker} · {row.label}",
            value=score_label,
            delta=trend_label,
            delta_color="off",
        )


def _render_missing_data(vm: IndexLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Missing Data / Refresh Needs")
    if not vm.missing_data:
        st.success("모든 종목에 대해 최신 bars / indicator 데이터가 존재합니다.")
        return
    st.caption(
        "다음 종목은 market_bars 또는 indicator_snapshots 가 비어 있습니다. "
        "System Ops에서 Market Refresh / Indicators 재계산을 실행하세요."
    )
    st.write(", ".join(vm.missing_data))


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _row_to_dict(row: IndexInstrumentVM) -> dict[str, object]:
    return {
        "Ticker": row.ticker,
        "Label": row.label,
        "Kind": row.kind,
        "Close": _format_decimal(row.latest_close),
        "RSI(14)": _format_decimal(row.rsi_14, places=2),
        "EMA20": _format_decimal(row.ema_20),
        "EMA60": _format_decimal(row.ema_60),
        "BB Position": _format_decimal(row.bb_position, places=4),
        "Vol z": _format_decimal(row.volume_z_score, places=2),
        "Momentum": _format_decimal(row.momentum_score, places=2),
        "Trend": row.trend_state or "—",
        "Score": _format_score(row.relative_strength_score),
        "Data": _DATA_STATUS_LABEL.get(row.data_status, row.data_status),
    }


def _format_decimal(value: Decimal | None, *, places: int = 4) -> str:
    if value is None:
        return "—"
    quant = Decimal(10) ** -places
    return f"{value.quantize(quant)}"


def _format_score(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return f"{value.quantize(Decimal('0.01'))}"
