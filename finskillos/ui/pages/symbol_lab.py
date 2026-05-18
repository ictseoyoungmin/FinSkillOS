"""Symbol Lab — Slice 09 individual-ticker page.

Renders the first usable per-symbol analysis screen: latest stored
``market_bars`` + ``indicator_snapshots`` for the selected ticker,
plus the active position context (if the ticker is held), related
alerts, and the latest ``MarketRegime`` row. Streamlit is imported
lazily inside ``render`` so the module stays importable in
non-Streamlit test contexts.

This page is read-only. Refresh / recalculation actions remain on
System Ops; Symbol Lab itself does not mutate the DB.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.components.formatting import (
    format_krw,
    format_pct,
    format_ratio,
)
from finskillos.ui.view_models import (
    SymbolLabViewModel,
    SymbolPositionVM,
    SymbolTechnicalVM,
    assert_symbol_lab_view_model_is_safe,
    build_symbol_lab_view_model,
    normalize_ticker,
)
from finskillos.ui.view_models.symbol_lab_vm import (
    DATA_STATUS_MISSING,
    DATA_STATUS_OK,
    DATA_STATUS_PARTIAL,
)

_DATA_STATUS_LABEL: dict[str, str] = {
    DATA_STATUS_OK: "정상",
    DATA_STATUS_PARTIAL: "부분",
    DATA_STATUS_MISSING: "누락",
}

_TICKER_INPUT_KEY = "symbol_lab_ticker"


def render(session: Session) -> None:
    import streamlit as st

    st.markdown("## Symbol Lab")
    st.caption(
        "개별 종목의 저장된 가격 / 지표 / 포지션 / Regime 컨텍스트를 모아서 "
        "서술적으로 점검합니다. 매수 / 매도 지시가 아닌 종목 상태 관찰용입니다."
    )

    ticker_input = _render_ticker_input(session)
    vm = build_symbol_lab_view_model(session, ticker=ticker_input)
    assert_symbol_lab_view_model_is_safe(vm)

    if vm.setup_hint:
        st.info(vm.setup_hint)

    _render_summary_header(vm)
    _render_technical_section(vm.technical)
    _render_recent_bars(vm)
    _render_position_section(vm.position)
    _render_alerts_section(vm)
    _render_regime_section(vm)
    _render_interpretation_section(vm)


# ---------------------------------------------------------------------------
# Ticker input
# ---------------------------------------------------------------------------


def _render_ticker_input(session: Session) -> str:
    import streamlit as st

    held = _held_tickers(session)
    default_value = st.session_state.get(_TICKER_INPUT_KEY, "")

    cols = st.columns([2, 3])
    with cols[0]:
        if held:
            choices = ("(직접 입력)",) + held
            picked = st.selectbox(
                "보유 종목에서 선택",
                choices,
                index=0,
                key="symbol_lab_picker",
            )
            if picked != "(직접 입력)":
                default_value = picked
                st.session_state[_TICKER_INPUT_KEY] = picked
        else:
            st.caption("보유 종목이 없습니다. ticker를 직접 입력하세요.")

    with cols[1]:
        raw = st.text_input(
            "Ticker",
            value=default_value,
            key=_TICKER_INPUT_KEY,
            help="예: TSLA, AAPL, NVDA — 입력값은 대문자로 정규화됩니다.",
        )

    return normalize_ticker(raw)


def _held_tickers(session: Session) -> tuple[str, ...]:
    from finskillos.db.repositories import AccountRepository, PositionRepository

    accounts = AccountRepository(session).list_all()
    if not accounts:
        return ()
    positions = PositionRepository(session).list_for_account(accounts[0].id)
    return tuple(sorted({p.ticker.upper() for p in positions}))


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------


def _render_summary_header(vm: SymbolLabViewModel) -> None:
    import streamlit as st

    if not vm.ticker:
        return

    cols = st.columns(3)
    cols[0].metric("Ticker", vm.ticker)
    cols[1].metric(
        "Latest close",
        _format_decimal(vm.technical.latest_close, places=4),
    )
    cols[2].metric(
        "Latest bar time",
        vm.technical.latest_time.strftime("%Y-%m-%d %H:%M %Z")
        if vm.technical.latest_time is not None
        else "—",
    )


# ---------------------------------------------------------------------------
# Technical
# ---------------------------------------------------------------------------


def _render_technical_section(technical: SymbolTechnicalVM) -> None:
    import streamlit as st

    st.markdown("### Technical Snapshot")
    if technical.data_status == DATA_STATUS_MISSING:
        st.info(
            f"{technical.ticker or 'ticker'}에 대한 저장된 market_bars / "
            "indicator_snapshots 데이터가 없습니다."
        )
        return

    rows = [
        {
            "RSI(14)": _format_decimal(technical.rsi_14, places=2),
            "EMA20": _format_decimal(technical.ema_20, places=4),
            "EMA60": _format_decimal(technical.ema_60, places=4),
            "EMA120": _format_decimal(technical.ema_120, places=4),
            "BB Position": _format_decimal(technical.bb_position, places=4),
            "Vol z": _format_decimal(technical.volume_z_score, places=2),
            "Momentum": _format_decimal(technical.momentum_score, places=2),
            "Trend": technical.trend_state or "—",
            "Data": _DATA_STATUS_LABEL.get(
                technical.data_status, technical.data_status
            ),
        }
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def _render_recent_bars(vm: SymbolLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Recent Bars")
    if not vm.has_recent_bars():
        st.caption(
            "저장된 market_bars가 없습니다. Candlestick 차트는 Slice 09에서 "
            "제공하지 않으며 후속 chart-polish 슬라이스로 이연됩니다."
        )
        return

    rows = [
        {
            "Time": bar.bar_time.strftime("%Y-%m-%d %H:%M"),
            "Open": _format_decimal(bar.open, places=4),
            "High": _format_decimal(bar.high, places=4),
            "Low": _format_decimal(bar.low, places=4),
            "Close": _format_decimal(bar.close, places=4),
            "Volume": _format_decimal(bar.volume, places=0),
        }
        for bar in vm.recent_bars
    ]
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption(
        "Candlestick / 볼륨 차트는 Slice 09 v0 범위 밖이며 후속 chart-polish "
        "슬라이스로 이연됩니다."
    )


# ---------------------------------------------------------------------------
# Position
# ---------------------------------------------------------------------------


def _render_position_section(position: SymbolPositionVM | None) -> None:
    import streamlit as st

    st.markdown("### Position Context")
    if position is None:
        st.info("현재 계좌에서 이 종목을 보유하고 있지 않습니다.")
        return

    cols = st.columns(3)
    cols[0].metric("Sector", position.sector or "—")
    cols[1].metric("Theme", position.theme or "—")
    cols[2].metric("Strategy", position.strategy_type or "—")

    cols2 = st.columns(3)
    cols2[0].metric("Market value", format_krw(position.market_value))
    cols2[1].metric("Quantity", _format_decimal(position.quantity, places=4))
    cols2[2].metric(
        "P&L",
        format_pct(position.pnl_pct) if position.pnl_pct is not None else "—",
    )

    cols3 = st.columns(2)
    cols3[0].metric(
        "Portfolio weight",
        format_ratio(position.portfolio_weight)
        if position.portfolio_weight is not None
        else "—",
    )
    if position.over_single_position_limit:
        cols3[1].error("단일 종목 한도(10,000,000 KRW) 초과")
    else:
        cols3[1].success("단일 종목 한도 이내")

    if position.thesis:
        st.markdown("**Thesis**")
        st.write(position.thesis)

    st.caption(
        "Average price / stop-loss / take-profit 참조 값은 현재 데이터 모델에 "
        "저장되어 있는 경우에만 표시됩니다. Slice 09 v0에서는 별도 표시를 "
        "이연합니다."
    )


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


def _render_alerts_section(vm: SymbolLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Symbol Alerts")
    if not vm.has_alerts():
        st.caption("No active symbol-specific alerts.")
        return

    rows = [
        {
            "Severity": alert.severity,
            "Date": alert.alert_date.isoformat(),
            "Guard": alert.guard_name,
            "Title": alert.title,
            "Message": alert.message,
        }
        for alert in vm.alerts
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# Regime + interpretation
# ---------------------------------------------------------------------------


def _render_regime_section(vm: SymbolLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Market Regime Context")
    cards.render_regime_card(vm.regime)


def _render_interpretation_section(vm: SymbolLabViewModel) -> None:
    import streamlit as st

    st.markdown("### Interpretation & Watchpoints")
    st.write(vm.interpretation)
    if vm.watchpoints:
        st.markdown("**Watchpoints**")
        for note in vm.watchpoints:
            st.markdown(f"- {note}")
    else:
        st.caption("표시할 watchpoint가 없습니다.")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_decimal(value: Decimal | None, *, places: int = 4) -> str:
    if value is None:
        return "—"
    if places == 0:
        return f"{value.quantize(Decimal('1'))}"
    quant = Decimal(10) ** -places
    return f"{value.quantize(quant)}"
