"""Application shell and controls for FinSkillOS."""

from __future__ import annotations

from html import escape
from typing import Sequence

import streamlit as st

from ui.components import panel


NAV_ITEMS = [
    ("Overview", "⌂"),
    ("Data Profile", "◎"),
    ("Return Analysis", "↗"),
    ("Risk Analysis", "◇"),
    ("Diversification", "◌"),
    ("Insights", "✦"),
    ("Applied Rules", "▣"),
    ("Reports", "▤"),
]

SAMPLE_DESCRIPTIONS = {
    "single_asset_price.csv": {
        "title": "단일 자산 가격 시계열",
        "body": "하나의 자산에 대해 날짜별 가격이 들어있는 기본 예시입니다. 누적수익률, drawdown, rolling volatility처럼 단일 가격 시계열에서 계산되는 지표를 확인하기 좋습니다.",
    },
    "multi_asset_portfolio.csv": {
        "title": "멀티 자산 포트폴리오 시계열",
        "body": "여러 자산의 날짜별 가격을 long format으로 담은 대표 데모 데이터입니다. 자산별 수익률, 상관관계, diversification, risk-return scatter 등 전체 대시보드 기능을 가장 풍부하게 확인할 수 있습니다.",
    },
    "mixed_schema_assets.csv": {
        "title": "혼합 컬럼명 스키마 매핑",
        "body": "`trade_dt`, `ticker_name`, `nav_value`처럼 표준 컬럼명이 아닌 입력을 자동으로 date, asset, price, volume 필드에 매핑하는 예시입니다. Auto Detect와 스키마 추론 품질을 확인할 때 사용합니다.",
    },
    "allocation_sample.csv": {
        "title": "보유 비중 / 자산 배분 스냅샷",
        "body": "날짜별 가격 시계열이 아니라 자산별 weight, sector, region을 담은 allocation 예시입니다. 포트폴리오 구성, 집중도, sector/region exposure를 확인하는 데 적합합니다.",
    },
}


def _html(value: object) -> str:
    return escape("" if value is None else str(value))


def _sample_description(sample_name: str) -> dict[str, str]:
    if sample_name == "샘플 없음":
        return {
            "title": "샘플 데이터 없음",
            "body": "샘플 CSV가 없거나 아직 선택되지 않았습니다. CSV Upload에서 직접 파일을 업로드하면 Auto Detect가 스키마를 추론합니다.",
        }
    return SAMPLE_DESCRIPTIONS.get(
        sample_name,
        {
            "title": "사용자 샘플 CSV",
            "body": "등록된 샘플 데이터입니다. Auto Detect가 컬럼 이름과 데이터 분포를 기준으로 날짜, 자산, 가격, 수익률, 비중 필드를 추론합니다.",
        },
    )


def _control_label(label: str, help_title: str, help_body: str) -> None:
    st.markdown(
        f"""
        <div class="fs-control-field-label">
          <span>{_html(label)}</span>
          <span class="fs-control-help" tabindex="0" aria-label="{_html(help_title)}">?</span>
          <div class="fs-control-help-card" role="tooltip">
            <div class="fs-control-help-title">{_html(help_title)}</div>
            <div class="fs-control-help-body">{_html(help_body)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_nav(active_tab: str, source_name: str, mode: str) -> str:
    """Render the product navigation shell and return the selected tab."""

    st.sidebar.markdown(
        """
        <div class="fs-brand">
          <div class="fs-logo-mark">FS</div>
          <div>
            <div class="fs-brand-title">FinSkill<span>OS</span></div>
            <div class="fs-brand-subtitle">Rule-governed analytics</div>
          </div>
        </div>
        <div class="fs-nav-label">Workspace</div>
        """,
        unsafe_allow_html=True,
    )

    labels = [item[0] for item in NAV_ITEMS]
    display_labels = [f"{icon}  {label}" for label, icon in NAV_ITEMS]
    label_by_display = dict(zip(display_labels, labels, strict=True))
    display_by_label = dict(zip(labels, display_labels, strict=True))
    if active_tab not in labels:
        active_tab = "Overview"
    selected_display = st.sidebar.radio(
        "Navigation",
        display_labels,
        index=display_labels.index(display_by_label[active_tab]),
        label_visibility="collapsed",
        key="active_tab_display",
    )

    st.sidebar.markdown(
        f"""
        <div class="fs-sidebar-footer">
          <div class="fs-portfolio-card">
            <div class="fs-sidebar-kicker">Dataset</div>
            <div class="fs-sidebar-value">{_html(source_name)}</div>
          </div>
          <div class="fs-portfolio-card">
            <div class="fs-sidebar-kicker">Analysis Mode</div>
            <div class="fs-sidebar-value">{_html(mode)}</div>
          </div>
          <div class="fs-sidebar-card">
            <div class="fs-sidebar-kicker">System</div>
            <div class="fs-sidebar-value"><span class="fs-status-dot"></span>All systems operational</div>
          </div>
          <div class="fs-user-row">
            <div class="fs-user-avatar">YM</div>
            <div class="fs-user-copy">
              <div class="fs-user-name">FinSkillOS Console</div>
              <div class="fs-user-plan">@ictseoyoungmin</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return label_by_display[selected_display]


def render_topbar(title: str, subtitle: str, active_tab: str, source_name: str, date_range: str) -> None:
    st.markdown(
        f"""
        <div class="fs-topbar-shell">
          <div class="fs-topbar">
            <div>
              <h1 class="fs-page-title">{_html(title)}</h1>
              <div class="fs-page-subtitle">{_html(subtitle)}</div>
              <div class="fs-badge-row">
                <span class="fs-badge fs-badge-live">Rule-Governed</span>
                <span class="fs-badge fs-badge-muted">Generated from Skills.md</span>
                <span class="fs-badge fs-badge-muted">{_html(active_tab)}</span>
              </div>
            </div>
            <div class="fs-badge-row">
              <span class="fs-badge fs-badge-muted">Dataset · {_html(source_name)}</span>
              <span class="fs-badge fs-badge-muted">Range · {_html(date_range)}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_topbar_controls(sample_files: Sequence[str]) -> dict[str, object]:
    """Render dataset, mode, rate, and action controls in the main app shell."""

    sample_options = list(sample_files)
    if sample_options:
        default_sample = "multi_asset_portfolio.csv"
        default_index = sample_options.index(default_sample) if default_sample in sample_options else 0
    else:
        sample_options = ["샘플 없음"]
        default_index = 0

    with panel("Analysis Controls", None, height=118, body_class="fs-control-shell"):
        row = st.columns(
            [1.48, 1.18, 0.98, 0.78, 0.82, 1.1],
            gap="small",
            vertical_alignment="bottom",
        )

        with row[0]:
            selected_sample = str(st.session_state.get("sample_dataset_select", sample_options[default_index]))
            description = _sample_description(selected_sample)
            _control_label("Sample Dataset", description["title"], description["body"])
            sample_name = st.selectbox(
                "Sample Dataset",
                sample_options,
                index=default_index,
                key="sample_dataset_select",
                label_visibility="collapsed",
            )

        with row[1]:
            _control_label(
                "CSV Upload",
                "사용자 CSV 업로드",
                "샘플 대신 직접 CSV 파일을 업로드하면 현재 파일을 우선 분석합니다. 파일명은 업로드 후 이 컨트롤 안에 표시됩니다.",
            )
            uploaded_file = st.file_uploader(
                "CSV Upload",
                type=["csv"],
                accept_multiple_files=False,
                key="csv_upload",
                label_visibility="collapsed",
            )

        with row[2]:
            _control_label("Mode", "분석 모드", "Auto Detect는 컬럼명과 데이터 분포를 바탕으로 가장 적합한 스키마를 자동 추론합니다.")
            mode = st.selectbox(
                "Mode",
                ["Auto Detect", "Single Asset", "Multi Asset", "Allocation"],
                key="analysis_mode_select",
                label_visibility="collapsed",
            )

        with row[3]:
            _control_label("Risk-Free Rate (%)", "무위험 수익률", "Sharpe ratio 등 위험 조정 지표 계산에 사용할 연 환산 무위험 수익률입니다.")
            risk_free_rate_pct = st.number_input(
                "Risk-Free Rate (%)",
                min_value=-100.0,
                max_value=100.0,
                value=0.0,
                step=0.25,
                format="%.2f",
                key="risk_free_rate_pct_input",
                label_visibility="collapsed",
            )
        risk_free_rate = risk_free_rate_pct / 100.0

        with row[4]:
            _control_label("Theme", "테마", "대시보드 전체의 Light/Dark 색상 체계를 전환합니다.")
            theme = st.selectbox(
                "Theme",
                ["Dark", "Light"],
                index=0,
                key="dashboard_theme",
                label_visibility="collapsed",
            )

        run_analysis = row[5].button(
            "Generate Dashboard",
            type="primary",
            icon=":material/analytics:",
            use_container_width=True,
        )

    return {
        "uploaded_file": uploaded_file,
        "sample_name": sample_name,
        "mode": mode,
        "risk_free_rate": risk_free_rate,
        "theme": theme,
        "run_analysis": run_analysis,
        "export_requested": False,
    }

def date_range_label(profile: dict[str, object] | None) -> str:
    if not profile:
        return "Awaiting data"
    start = profile.get("start_date")
    end = profile.get("end_date")
    if start and end:
        return f"{start} - {end}"
    return str(profile.get("frequency", "Detected after load")).title()
