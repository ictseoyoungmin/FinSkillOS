"""Risk Firewall page — full guard ladder + active alerts."""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.view_models import build_control_room_view_model


def render(session: Session) -> None:
    import streamlit as st

    vm = build_control_room_view_model(session, persist_alerts=False)

    st.markdown("## Risk Firewall")
    st.caption(
        "8개 가드 결과를 한 화면에서 점검하세요. "
        "WARN 이상 결과는 자동으로 alerts 테이블에 누적됩니다."
    )

    if not vm.has_account:
        st.info(vm.setup_hint or "기본 계좌가 없어 가드를 실행할 수 없습니다.")
        return

    cards.render_guard_report_card(vm)
    cards.render_active_alerts_card(vm.alerts)
