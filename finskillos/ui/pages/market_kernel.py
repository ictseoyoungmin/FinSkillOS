"""Market Kernel page — latest regime + factors detail."""

from __future__ import annotations

from sqlalchemy.orm import Session

from finskillos.ui.components import cards
from finskillos.ui.view_models import build_control_room_view_model


def render(session: Session) -> None:
    import streamlit as st

    vm = build_control_room_view_model(session, persist_alerts=False)

    st.markdown("## Market Kernel")
    st.caption(
        "최신 Regime 분류, 신뢰도, 운영 모드, 그리고 긍정 / 위험 factor를 한 화면에서 확인하세요."
    )

    cards.render_regime_card(vm.regime)

    if vm.regime is None:
        st.markdown(
            "> Regime 데이터가 없으면 System Ops 탭의 'Regime 재계산'을 실행해 "
            "지표 기반 분류를 트리거할 수 있습니다."
        )
