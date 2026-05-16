from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from engine.chart_planner import plan_charts
from engine.data_profiler import profile_dataframe
from engine.history_enricher import fetch_history_for_holdings, is_holdings_snapshot
from engine.insight_engine import generate_insights
from engine.metrics import compute_metrics
from engine.rule_engine import RuleAuditLog
from engine.schema_mapper import infer_schema
from ui.layout import date_range_label, render_sidebar_nav, render_topbar, render_topbar_controls
from ui.tabs import (
    render_applied_rules_tab,
    render_data_profile_tab,
    render_diversification_tab,
    render_insights_tab,
    render_overview_dashboard,
    render_reports_tab,
    render_return_analysis_tab,
    render_risk_analysis_tab,
)
from ui.theme import apply_dashboard_style
from ui.components import vspace

APP_ROOT = Path(__file__).resolve().parent
SAMPLE_DATA_DIR = APP_ROOT / "sample_data"
SKILLS_DIR = APP_ROOT / "FinSkillOS_skills"


def list_sample_files() -> list[str]:
    if not SAMPLE_DATA_DIR.exists():
        return []
    return sorted(path.name for path in SAMPLE_DATA_DIR.glob("*.csv"))


def read_uploaded_or_sample(uploaded_file, sample_name: str | None) -> tuple[pd.DataFrame | None, str]:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), uploaded_file.name

    if sample_name and sample_name != "샘플 없음":
        sample_path = SAMPLE_DATA_DIR / sample_name
        if sample_path.exists():
            return pd.read_csv(sample_path), sample_name

    return None, "데이터 미선택"


def build_initial_audit_log(mode: str, source_name: str) -> RuleAuditLog:
    audit = RuleAuditLog()
    audit.add(
        rule_id="AUTO-STRUCT-001",
        step="project_skeleton",
        condition="FinSkillOS MVP requires the documented app and engine layout.",
        action="Initialized Streamlit app, engine package, sample_data, and reports folders.",
        result="Slice 1 project skeleton is active.",
    )
    audit.add(
        rule_id="DASH-001",
        step="dashboard_layout",
        condition="Default dashboard section order is required.",
        action="Rendered the initial sections in the Skill-defined sequence.",
        result="Header, Data Profile, Schema Mapping, Summary, Analysis, Insights, Rules, and Export placeholders are visible.",
    )
    audit.add(
        rule_id="DASH-002",
        step="dashboard_header",
        condition="Header must include service name, description, mode, and dataset name.",
        action="Displayed FinSkillOS header metadata.",
        result=f"Mode={mode}; Dataset={source_name}.",
    )
    audit.add(
        rule_id="DASH-003",
        step="sidebar_controls",
        condition="Sidebar must provide upload, sample selection, analysis mode, risk-free rate, run, and export controls.",
        action="Rendered required sidebar controls.",
        result="All required sidebar controls are present.",
    )
    audit.add(
        rule_id="AUTO-APP-002",
        step="rule_trace_visibility",
        condition="Applied Skill Rules must be visible in the web UI.",
        action="Rendered an Applied Skill Rules table.",
        result="Rule audit records are displayed at the bottom of the dashboard.",
    )
    return audit


def add_chart_rules(audit: RuleAuditLog, chart_plan: list[dict[str, object]]) -> None:
    for chart in chart_plan:
        audit.add(
            rule_id=str(chart["rule_id"]),
            step="chart_planning",
            condition=str(chart["reason"]),
            action=f"Plan chart `{chart['chart_id']}`.",
            result="Selected for rendering." if chart.get("available") else "Not rendered; prerequisites are unavailable.",
        )


@st.cache_data(ttl=900, show_spinner=False)
def _cached_holdings_history(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return fetch_history_for_holdings(df)


def enrich_holdings_snapshot(df: pd.DataFrame, audit: RuleAuditLog) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Attach fetched price history when an uploaded CSV is a holdings snapshot."""

    if not is_holdings_snapshot(df):
        return df, pd.DataFrame()

    history_df, log_df = _cached_holdings_history(df)
    ok_count = int((log_df.get("status", pd.Series(dtype=str)) == "ok").sum()) if not log_df.empty else 0
    if history_df.empty:
        audit.add(
            rule_id="DATA-HISTORY-001",
            step="history_enrichment",
            condition="Holdings snapshot includes ticker fields but no historical price rows.",
            action="Attempt optional yfinance price-history enrichment.",
            result="No price history was attached; allocation snapshot analysis will be used.",
            severity="WARNING",
        )
        return df, log_df

    audit.add(
        rule_id="DATA-HISTORY-001",
        step="history_enrichment",
        condition="Holdings snapshot includes ticker fields.",
        action="Fetch recent daily price history and convert it to `date, asset, price, weight` format.",
        result=f"{len(history_df):,} price rows attached for {ok_count} ticker(s).",
    )
    return history_df, log_df


def main() -> None:
    st.set_page_config(
        page_title="FinSkillOS",
        page_icon="FS",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_dashboard_style(theme=str(st.session_state.get("dashboard_theme", "Dark")))

    header_slot = st.container()
    controls_slot = st.container()
    with controls_slot:
        controls = render_topbar_controls(list_sample_files())
    df, source_name = read_uploaded_or_sample(
        controls["uploaded_file"],
        controls["sample_name"],
    )
    mode = str(controls["mode"])
    audit = build_initial_audit_log(mode=mode, source_name=source_name)
    profile = None
    schema = None
    metrics = None
    insights = None
    analysis_result = None
    chart_plan: list[dict[str, object]] = []
    if df is not None:
        df, history_log = enrich_holdings_snapshot(df, audit)
        profile = profile_dataframe(df)
        audit.extend(profile["applied_rules"])
        schema = infer_schema(df, profile, mode=mode)
        audit.extend(schema["applied_rules"])
        metrics = compute_metrics(
            schema["standardized_df"],
            schema,
            risk_free_rate=float(controls["risk_free_rate"]),
            profile=profile,
        )
        audit.extend(metrics["applied_rules"])
        chart_plan = plan_charts(schema, metrics)
        add_chart_rules(audit, chart_plan)
        insights = generate_insights(metrics, profile, schema)
        audit.extend(insights["applied_rules"])
        analysis_result = {
            "source_name": source_name,
            "mode": mode,
            "profile": profile,
            "schema": schema,
            "metrics": metrics,
            "chart_plan": chart_plan,
            "insights": insights,
            "applied_rules": audit.deduplicated_records(),
        }

    active_tab = render_sidebar_nav(
        active_tab="Overview",
        source_name=source_name,
        mode=mode,
    )
    with header_slot:
        render_topbar(
            title="Investment Analytics Dashboard" if active_tab == "Overview" else active_tab,
            subtitle="Skill-Governed Investment Analytics Dashboard",
            active_tab=active_tab,
            source_name=source_name,
            date_range=date_range_label(profile),
        )
        vspace(8)

    if controls["run_analysis"]:
        st.success("Analysis refreshed for the current dataset.")
    elif controls["export_requested"]:
        st.warning("Report export is not available yet.")

    if active_tab == "Overview":
        render_overview_dashboard(
            df=df,
            source_name=source_name,
            audit=audit,
            profile=profile,
            schema=schema,
            metrics=metrics,
            insights=insights,
            analysis_result=analysis_result,
        )
    elif active_tab == "Data Profile":
        render_data_profile_tab(
            df=df,
            audit=audit,
            profile=profile,
            schema=schema,
        )
    elif active_tab == "Return Analysis":
        render_return_analysis_tab(
            df=df,
            audit=audit,
            metrics=metrics,
            insights=insights,
            profile=profile,
        )
    elif active_tab == "Risk Analysis":
        render_risk_analysis_tab(
            df=df,
            audit=audit,
            metrics=metrics,
            insights=insights,
            profile=profile,
        )
    elif active_tab == "Diversification":
        render_diversification_tab(
            df=df,
            audit=audit,
            schema=schema,
            metrics=metrics,
            insights=insights,
        )
    elif active_tab == "Insights":
        render_insights_tab(
            df=df,
            source_name=source_name,
            audit=audit,
            schema=schema,
            metrics=metrics,
            insights=insights,
        )
    elif active_tab == "Applied Rules":
        render_applied_rules_tab(
            df=df,
            audit=audit,
        )
    elif active_tab == "Reports":
        render_reports_tab(
            df=df,
            source_name=source_name,
            audit=audit,
            profile=profile,
            schema=schema,
            metrics=metrics,
            analysis_result=analysis_result,
        )

    with st.expander("Skills.md Implementation Reference", expanded=False):
        st.write("This app follows the Rule IDs and implementation contracts from the `FinSkillOS_skills` documentation set.")
        st.write(f"Skills directory: `{SKILLS_DIR}`")


if __name__ == "__main__":
    main()
