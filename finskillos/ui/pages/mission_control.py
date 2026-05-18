"""Mission Control page — goal-progress focus view."""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.view_models import build_control_room_view_model


def render(session: Session) -> None:
    import streamlit as st

    vm = build_control_room_view_model(session, persist_alerts=False)

    st.markdown("## Mission Control")
    st.caption(
        "57,000,000 KRW → 100,000,000 KRW 도달까지의 진행 상태와 운영 모드를 점검하세요."
    )

    if not vm.has_account:
        st.info(vm.setup_hint or "기본 계좌가 설정되어 있지 않습니다.")
        return

    cards.render_goal_card(vm.goal)
    cards.render_portfolio_card(vm.portfolio)
