"""Control Room page — Slice 07 first usable cockpit screen.

Renders the four core cards (Goal / Portfolio / Regime / Risk Firewall
+ Active Alerts) in a single read pass from
``ControlRoomViewModel``. The page never touches services directly;
all data flows through the view-model builder.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.view_models import build_control_room_view_model


def render(session: Session) -> None:
    import streamlit as st

    vm = build_control_room_view_model(session, persist_alerts=False)

    cards.render_status_banner(vm)

    if not vm.has_account:
        st.info(vm.setup_hint or "기본 계좌가 설정되어 있지 않습니다.")
        return

    top_left, top_right = st.columns([1, 1])
    with top_left:
        cards.render_goal_card(vm.goal)
    with top_right:
        cards.render_regime_card(vm.regime)

    cards.render_portfolio_card(vm.portfolio)
    cards.render_guard_report_card(vm)
    cards.render_active_alerts_card(vm.alerts)
