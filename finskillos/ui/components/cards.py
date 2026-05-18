"""Streamlit card / panel widgets used by the Slice-07 Control Room.

Each function takes a view-model fragment and renders a single card.
Streamlit is imported lazily inside each function so importing this
module from a non-Streamlit context (tests, type-check) does not
trigger a ``streamlit`` import.
"""

from __future__ import annotations

from finskillos.ui.components.formatting import (
    format_krw,
    format_pct,
    format_ratio,
    risk_color,
    status_emoji,
    status_label,
)
from finskillos.ui.view_models import (
    AlertSummary,
    ControlRoomViewModel,
    GoalSummary,
    GuardSummary,
    PortfolioSummaryVM,
    RegimeSummary,
)

# ---------------------------------------------------------------------------
# Status banner
# ---------------------------------------------------------------------------


def render_status_banner(vm: ControlRoomViewModel) -> None:
    import streamlit as st

    if not vm.has_account:
        st.warning(
            "기본 계좌가 비어 있습니다. System Ops 탭에서 샘플 계좌를 생성하면 "
            "Control Room이 즉시 활성화됩니다."
        )
        return

    color = risk_color(vm.overall_risk_level)
    st.markdown(
        f"""
        <div style="
            padding: 14px 18px;
            background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
            border: 1px solid {color};
            border-radius: 10px;
            margin-bottom: 12px;">
            <div style="font-size:12px; letter-spacing:0.2em; color:#a8c8e8;">
                FINSKILLOS · CONTROL ROOM · {vm.account_name}
            </div>
            <div style="font-size:22px; font-weight:600; margin-top:4px;">
                {status_emoji(vm.overall_status)} 종합 상태:
                {status_label(vm.overall_status)} · 위험 레벨
                <span style="color:{color};">{vm.overall_risk_level}</span>
            </div>
            <div style="font-size:12px; color:#a8c8e8; margin-top:6px;">
                생성 시각 {vm.generated_at.strftime('%Y-%m-%d %H:%M %Z')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Mission Control — Goal card
# ---------------------------------------------------------------------------


def render_goal_card(goal: GoalSummary | None) -> None:
    import streamlit as st

    st.subheader("Mission Control · 목표 진행률")
    if goal is None:
        st.info("아직 목표 데이터가 없습니다.")
        return

    cols = st.columns(3)
    cols[0].metric("현재 자산", format_krw(goal.current_value))
    cols[1].metric("목표 자산", format_krw(goal.target_value))
    cols[2].metric("잔여 목표", format_krw(goal.remaining_value))

    progress_ratio = min(1.0, float(goal.progress_pct) / 100.0)
    st.progress(progress_ratio, text=f"진행률 {format_pct(goal.progress_pct)}")

    badge_color = "#00cc66" if not goal.early_stop_triggered else "#ff3b5c"
    st.markdown(
        f"""
        <div style="margin-top:6px;">
            <span style="background:{badge_color}; color:white;
                padding:3px 10px; border-radius:12px; font-size:11px;
                letter-spacing:0.15em;">
                {goal.goal_mode}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if goal.early_stop_triggered:
        st.success(
            "목표 도달 — 챌린지 완료 단계입니다. "
            "추가 공격적 운용보다 이익 보호가 우선되는 단계입니다."
        )


# ---------------------------------------------------------------------------
# Portfolio summary card
# ---------------------------------------------------------------------------


def render_portfolio_card(portfolio: PortfolioSummaryVM | None) -> None:
    import streamlit as st

    st.subheader("Portfolio Snapshot")
    if portfolio is None or portfolio.total_value == 0:
        st.info("포트폴리오 입력이 없습니다. CSV 또는 수동 입력 후 다시 점검하세요.")
        return

    cols = st.columns(3)
    cols[0].metric("총 평가금액", format_krw(portfolio.total_value))
    cols[1].metric("현금", format_krw(portfolio.cash_value))
    cols[2].metric("포지션 수", portfolio.position_count)

    cols2 = st.columns(2)
    cols2[0].metric(
        "최대 포지션",
        portfolio.largest_position_ticker or "—",
        format_ratio(portfolio.largest_position_weight),
    )
    if portfolio.over_single_limit_tickers:
        cols2[1].error(
            "단일 종목 한도 초과: " + ", ".join(portfolio.over_single_limit_tickers)
        )
    else:
        cols2[1].success("단일 종목 한도 이내")

    if portfolio.sector_exposure:
        st.markdown("**섹터 노출**")
        rows = sorted(
            portfolio.sector_exposure.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )
        st.table(
            [
                {"섹터": key, "비중": format_ratio(value)}
                for key, value in rows
            ]
        )


# ---------------------------------------------------------------------------
# Market Kernel — Regime card
# ---------------------------------------------------------------------------


def render_regime_card(regime: RegimeSummary | None) -> None:
    import streamlit as st

    st.subheader("Market Kernel · 시장 Regime")
    if regime is None:
        st.info(
            "아직 평가된 regime이 없습니다. System Ops 탭의 'Regime 재계산'을 "
            "실행하면 최신 indicator를 기반으로 분류합니다."
        )
        return

    color = risk_color(regime.risk_level)
    st.markdown(
        f"""
        <div style="padding:10px 14px; border-left:4px solid {color};
             background:rgba(255,255,255,0.03); border-radius:6px;">
            <div style="font-size:11px; color:#a8c8e8; letter-spacing:0.2em;">
                REGIME · {regime.decision_mode}
            </div>
            <div style="font-size:22px; font-weight:600; color:{color};">
                {regime.regime}
            </div>
            <div style="font-size:12px; color:#a8c8e8;">
                Confidence {format_pct(regime.confidence, places=0)} ·
                Risk Level {regime.risk_level}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if regime.summary:
        st.markdown(f"> {regime.summary}")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Positive factors**")
        if regime.positive_factors:
            for f in regime.positive_factors:
                st.markdown(f"- {f}")
        else:
            st.caption("관찰된 긍정 신호가 없습니다.")
    with cols[1]:
        st.markdown("**Risk factors**")
        if regime.risk_factors:
            for f in regime.risk_factors:
                st.markdown(f"- {f}")
        else:
            st.caption("관찰된 위험 신호가 없습니다.")

    with st.expander("해석 카드 (What happened / What it means / Watch next)"):
        if regime.what_happened:
            st.markdown(f"**What happened?** {regime.what_happened}")
        if regime.what_it_means:
            st.markdown(f"**What does it mean?** {regime.what_it_means}")
        if regime.watch_next:
            st.markdown("**Watch next**")
            for w in regime.watch_next:
                st.markdown(f"- {w}")


# ---------------------------------------------------------------------------
# Risk Firewall — Guard report card
# ---------------------------------------------------------------------------


def render_guard_report_card(
    vm: ControlRoomViewModel,
) -> None:
    import streamlit as st

    st.subheader("Risk Firewall · 가드 결과")
    if not vm.has_account:
        st.info("계좌가 없으므로 가드를 실행할 수 없습니다.")
        return
    if not vm.guard_report:
        st.info("아직 가드 결과가 없습니다.")
        return

    st.caption(
        f"종합 상태 {status_label(vm.overall_status)} · "
        f"위험 레벨 {vm.overall_risk_level}"
    )
    rows = [
        {
            "Guard": guard.guard_name,
            "Status": f"{status_emoji(guard.status)} {status_label(guard.status)}",
            "Risk": guard.risk_level,
            "Title": guard.title,
        }
        for guard in vm.guard_report
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)

    for guard in vm.guard_report:
        if guard.status in {"PASS", "INFO"}:
            continue
        _render_guard_detail(guard)


def _render_guard_detail(guard: GuardSummary) -> None:
    import streamlit as st

    color = risk_color(guard.risk_level)
    st.markdown(
        f"""
        <div style="margin-top:8px; padding:10px 12px;
             border-left:4px solid {color}; background:rgba(255,255,255,0.02);
             border-radius:6px;">
            <div style="font-size:11px; color:#a8c8e8; letter-spacing:0.15em;">
                {guard.guard_name} · {guard.risk_level}
            </div>
            <div style="font-size:14px; font-weight:600;">{guard.title}</div>
            <div style="font-size:13px; color:#a8c8e8; margin-top:4px;">
                {guard.message}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if guard.watch_next:
        with st.expander("Watch next"):
            for w in guard.watch_next:
                st.markdown(f"- {w}")


# ---------------------------------------------------------------------------
# Active alerts card
# ---------------------------------------------------------------------------


def render_active_alerts_card(alerts: tuple[AlertSummary, ...]) -> None:
    import streamlit as st

    st.subheader("Active Alerts")
    if not alerts:
        st.success("미해결 alert이 없습니다.")
        return

    st.dataframe(
        [
            {
                "Severity": a.severity,
                "Date": a.alert_date.isoformat(),
                "Guard": a.guard_name,
                "Title": a.title,
                "Message": a.message or "",
            }
            for a in alerts
        ],
        hide_index=True,
        use_container_width=True,
    )
