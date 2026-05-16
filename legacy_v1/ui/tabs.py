"""Tab-level renderers for the FinSkillOS dashboard."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import numpy as np
import streamlit as st

from engine.metrics import format_percent, format_ratio
from engine.report_builder import build_html_report
from engine.rule_engine import RuleAuditLog
from ui.charts import (
    render_allocation_chart,
    render_correlation_heatmap,
    render_cumulative_return_chart,
    render_drawdown_chart,
    render_frequency_coverage_chart,
    render_missing_values_chart,
    render_monthly_returns_heatmap,
    render_return_distribution,
    render_var_cvar_distribution,
    render_risk_contribution_chart,
    render_risk_return_scatter,
    render_rolling_return_chart,
    render_rolling_volatility_chart,
)
from ui.components import (
    compact_data_table,
    empty_state,
    insight_card,
    key_value_table,
    metric_card,
    onboarding_state,
    panel,
    rule_card,
    rule_chip,
    rule_validation_list,
    status_badge,
    summary_stat_card,
    vspace,
)


def _schema_compact_table(schema: dict[str, Any] | None, profile: dict[str, Any] | None) -> pd.DataFrame:
    if not schema:
        return pd.DataFrame(
            [
                {"item": "Schema", "value": "Awaiting dataset"},
                {"item": "Frequency", "value": "N/A"},
                {"item": "Rows", "value": "N/A"},
            ]
        )

    mapping = schema.get("mapping", {})
    rows = [
        {"item": "Detected Schema", "value": schema.get("schema_type", "unknown")},
        {"item": "Date Column", "value": mapping.get("date", {}).get("source", "N/A")},
        {"item": "Asset Column", "value": mapping.get("asset", {}).get("source", "N/A")},
        {"item": "Price Column", "value": mapping.get("price", {}).get("source", "N/A")},
        {"item": "Return Column", "value": mapping.get("return", {}).get("source", "N/A")},
    ]
    if profile:
        rows.extend(
            [
                {"item": "Frequency", "value": str(profile.get("frequency", "unknown")).title()},
                {"item": "Rows", "value": f"{int(profile.get('row_count', 0)):,}"},
            ]
        )
    return pd.DataFrame(rows)


def _quality_summary(profile: dict[str, Any] | None) -> str:
    if not profile:
        return "Awaiting data"
    warnings = profile.get("quality_warnings", [])
    if warnings:
        return f"{len(warnings)} warning(s)"
    return "No blocking warnings"


def _asset_count(metrics: dict[str, Any] | None, schema: dict[str, Any] | None) -> str:
    if metrics:
        rows = metrics.get("asset_metrics", [])
        if rows:
            return f"{len(rows):,}"
    std_df = schema.get("standardized_df") if schema else None
    if isinstance(std_df, pd.DataFrame) and "asset" in std_df.columns:
        return f"{std_df['asset'].nunique(dropna=True):,}"
    return "N/A"


def _date_range(schema: dict[str, Any] | None) -> str:
    std_df = schema.get("standardized_df") if schema else None
    if not isinstance(std_df, pd.DataFrame) or "date" not in std_df.columns:
        return "N/A"
    dates = pd.to_datetime(std_df["date"], errors="coerce").dropna()
    if dates.empty:
        return "N/A"
    return f"{dates.min().date()} - {dates.max().date()}"


def _missing_summary(profile: dict[str, Any] | None) -> tuple[str, str]:
    if not profile:
        return "N/A", "Awaiting profile"
    rates = profile.get("missing_rates", {})
    row_count = int(profile.get("row_count", 0))
    missing_cells = int(sum(rate * row_count for rate in rates.values()))
    total_cells = max(row_count * len(rates), 1)
    return f"{missing_cells:,}", f"{missing_cells / total_cells:.2%} of cells"


def _average_correlation(metrics: dict[str, Any] | None) -> float | None:
    if not metrics:
        return None
    corr = metrics.get("correlation_matrix")
    if not isinstance(corr, pd.DataFrame) or corr.empty or corr.shape[0] < 2:
        return None
    values = corr.to_numpy(dtype=float)
    mask = ~np.eye(values.shape[0], dtype=bool)
    off_diag = values[mask]
    off_diag = off_diag[~np.isnan(off_diag)]
    if len(off_diag) == 0:
        return None
    return float(off_diag.mean())


def _allocation_rows(schema: dict[str, Any] | None) -> pd.DataFrame:
    std_df = schema.get("standardized_df") if schema else None
    if not isinstance(std_df, pd.DataFrame) or not {"asset", "weight"}.issubset(std_df.columns):
        return pd.DataFrame()
    return std_df.dropna(subset=["asset", "weight"]).copy()


def _largest_weight(schema: dict[str, Any] | None) -> tuple[str, str]:
    rows = _allocation_rows(schema)
    if rows.empty:
        return "N/A", "No allocation weights"
    idx = rows["weight"].astype(float).idxmax()
    row = rows.loc[idx]
    return format_percent(float(row["weight"])), str(row["asset"])


def _cash_exposure(schema: dict[str, Any] | None) -> str:
    rows = _allocation_rows(schema)
    if rows.empty:
        return "N/A"
    mask = rows["asset"].astype(str).str.contains("cash", case=False, na=False)
    if not mask.any():
        return "0.00%"
    return format_percent(float(rows.loc[mask, "weight"].sum()))


def _rule_cards_for_prefix(audit: RuleAuditLog, prefixes: set[str], limit: int = 4) -> None:
    records = [record for record in audit.deduplicated_records() if str(record.get("prefix")) in prefixes]
    if not records:
        empty_state("No Matching Rules", f"No rules with prefixes {', '.join(sorted(prefixes))} were recorded.")
        return
    columns = st.columns(min(limit, len(records)))
    for column, record in zip(columns, records[:limit], strict=False):
        with column:
            rule_card(
                rule_id=str(record.get("rule_id", "RULE")),
                title=str(record.get("step", "rule")),
                description=str(record.get("result", "")),
                status="Passed" if record.get("severity") != "WARNING" else "Review",
                severity=str(record.get("severity", "INFO")),
            )


def _rule_validation_list_for_prefix(audit: RuleAuditLog, prefixes: set[str], limit: int = 6) -> None:
    records = [record for record in audit.deduplicated_records() if str(record.get("prefix")) in prefixes]
    rule_validation_list(records, limit=limit)


def _format_metric_table(df: pd.DataFrame, percent_cols: set[str] | None = None, ratio_cols: set[str] | None = None) -> pd.DataFrame:
    percent_cols = percent_cols or set()
    ratio_cols = ratio_cols or set()
    formatted = df.copy()
    for col in formatted.columns:
        if col in percent_cols:
            formatted[col] = formatted[col].map(lambda value: format_percent(value))
        elif col in ratio_cols:
            formatted[col] = formatted[col].map(lambda value: format_ratio(value))
        else:
            formatted[col] = formatted[col].astype(str)
    return formatted


def _require_analysis(df: pd.DataFrame | None, metrics: dict[str, Any] | None = None) -> bool:
    if df is None or metrics is None:
        onboarding_state(
            "Select a Dataset to Continue",
            "Choose a bundled sample or upload a CSV from the analysis controls. This tab will populate after the pipeline runs.",
            [
                "Use Sample Dataset for the fastest demo path.",
                "Choose Auto Detect unless you need to force a schema mode.",
                "Review unavailable panels for exact prerequisite reasons.",
            ],
        )
        return False
    return True


def _analysis_available(df: pd.DataFrame | None) -> bool:
    if df is None:
        onboarding_state(
            "Select a Dataset to Continue",
            "Choose a bundled sample or upload a CSV from the analysis controls. Governance tabs populate after the pipeline runs.",
            [
                "Run analysis to generate insights, rules, and report exports.",
                "Applied Rules will show traceability by rule prefix.",
                "Reports will expose the current HTML export package.",
            ],
        )
        return False
    return True


def _rule_records(audit: RuleAuditLog) -> list[dict[str, Any]]:
    return [dict(record) for record in audit.deduplicated_records()]


def _rule_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    warnings = [record for record in records if record.get("severity") == "WARNING"]
    blocked = [record for record in records if record.get("severity") == "ERROR"]
    prefixes = {str(record.get("prefix")) for record in records}
    required = {"DATA", "SCHEMA", "METRIC", "VIS", "INSIGHT", "SAFE"}
    return {
        "executed": len(records),
        "passed": len(records) - len(warnings) - len(blocked),
        "warnings": len(warnings),
        "blocked": len(blocked),
        "coverage": len(prefixes & required),
        "required": len(required),
        "prefixes": prefixes,
    }


def _selected_insight(items: list[dict[str, Any]]) -> tuple[int, dict[str, Any] | None]:
    if not items:
        return 0, None
    max_index = len(items) - 1
    current = int(st.session_state.get("selected_insight_index", 0))
    current = max(0, min(current, max_index))
    st.session_state["selected_insight_index"] = current
    return current, items[current]


def _rule_reference_rows(rule_ids: list[str], records: list[dict[str, Any]]) -> pd.DataFrame:
    if not rule_ids:
        return pd.DataFrame()
    matched = [
        {
            "rule_id": record.get("rule_id"),
            "step": record.get("step"),
            "severity": record.get("severity"),
            "result": record.get("result"),
        }
        for record in records
        if record.get("rule_id") in set(rule_ids)
    ]
    if matched:
        return pd.DataFrame(matched)
    return pd.DataFrame([{"rule_id": rule_id, "step": "Referenced by insight", "severity": "INFO", "result": "No matching audit row"} for rule_id in rule_ids])


def _report_library(source_name: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"report_name": "Investment Analytics Report", "dataset": source_name, "status": "Latest", "format": "HTML"},
            {"report_name": "Risk Analysis Extract", "dataset": source_name, "status": "Generated", "format": "HTML"},
            {"report_name": "Rule Audit Export", "dataset": source_name, "status": "Generated", "format": "CSV/JSON"},
        ]
    )


def render_overview_dashboard(
    df: pd.DataFrame | None,
    source_name: str,
    audit: RuleAuditLog,
    profile: dict[str, Any] | None,
    schema: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    insights: dict[str, Any] | None,
    analysis_result: dict[str, Any] | None,
) -> None:
    """Render the product-style overview dashboard."""

    if df is None or metrics is None:
        onboarding_state(
            "Select a Dataset to Generate the Overview",
            "Use the analysis controls above to upload a CSV or choose a bundled sample. The overview will populate with KPI cards, charts, insights, and applied rule traceability.",
            [
                "Try multi_asset_portfolio.csv for the richest chart demo.",
                "Try mixed_schema_assets.csv to show schema adaptation.",
                "Try allocation_sample.csv to validate allocation states.",
            ],
        )
        return

    summary = metrics.get("summary", {})
    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Total Return", format_percent(summary.get("total_return")), "Total over selected period", "teal", "↗")
    with kpi_cols[1]:
        metric_card("Annualized Return", format_percent(summary.get("annualized_return")), "Compounded per year", "teal", "⟳")
    with kpi_cols[2]:
        metric_card("Volatility (Ann.)", format_percent(summary.get("annualized_volatility")), "Standard deviation", "blue", "~")
    with kpi_cols[3]:
        metric_card("Max Drawdown", format_percent(summary.get("max_drawdown")), "From peak to trough", "red", "↘")
    with kpi_cols[4]:
        metric_card("Sharpe Ratio", format_ratio(summary.get("sharpe_ratio")), "Risk-adjusted return", "purple", "Σ")
    with kpi_cols[5]:
        risk_level = str(summary.get("risk_level", "UNKNOWN"))
        metric_card("Risk Level", risk_level, "Rule-based classification", "amber", "◇")

    vspace(18)

    top_left, top_mid, top_right = st.columns([1.45, 1.0, 0.88])
    with top_left:
        with panel("Executive Summary", "Cumulative return over time", height=360):
            render_cumulative_return_chart(metrics, height=280)
    with top_mid:
        with panel("Risk Analysis", "Drawdown behavior", height=360):
            render_drawdown_chart(metrics, height=280)
    with top_right:
        with panel("Data Profile", f"Source: {source_name}", height=360, scroll=True):
            profile_rows = _schema_compact_table(schema, profile).astype(str).to_dict("records")
            profile_rows.extend(
                [
                    {"item": "Assets", "value": _asset_count(metrics, schema)},
                    {"item": "Quality", "value": _quality_summary(profile)},
                ]
            )
            key_value_table(profile_rows)

    lower_left, lower_mid, lower_right = st.columns([1.08, 1.08, 1.15])
    with lower_left:
        with panel("Correlation & Diversification", "Asset relationship overview", height=340):
            render_correlation_heatmap(metrics, height=245)
    with lower_mid:
        with panel("Risk vs. Return", "Annualized return versus volatility", height=340):
            render_risk_return_scatter(metrics, height=245)
    with lower_right:
        with panel("Rule-Based Insights", "Fact, interpretation, and caution generated from Skills.md rules", height=340, scroll=True):
            vspace(14)
            items = (insights or {}).get("insights", [])
            if not items:
                empty_state("No Insights Generated", "The insight engine did not produce evidence-linked cards for this dataset.")
            for item in items[:3]:
                insight_card(
                    category=str(item.get("category", "Insight")),
                    fact=str(item.get("fact", "")),
                    interpretation=str(item.get("interpretation", "")),
                    caution=str(item.get("caution", "")),
                    severity=str(item.get("severity", "INFO")),
                    compact=True,
                )
                vspace(14)

    records = audit.deduplicated_records()
    coverage = audit.has_prefixes(["DATA", "SCHEMA", "METRIC", "VIS", "INSIGHT", "SAFE"])
    coverage_value = f"{sum(coverage.values())}/{len(coverage)} categories"
    schema_value = str(schema.get("schema_type", "unknown") if schema else "unknown")

    def _fs_escape(value: object) -> str:
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _overview_footer_stat(label: str, value: str, caption: str, tone: str = "teal") -> None:
        st.markdown(
            f"""
            <div class="fs-overview-stat-card" data-tone="{_fs_escape(tone)}">
              <div class="fs-overview-stat-kicker">{_fs_escape(label)}</div>
              <div class="fs-overview-stat-value">{_fs_escape(value)}</div>
              <div class="fs-overview-stat-caption">{_fs_escape(caption)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="fs-row-spacer"></div>', unsafe_allow_html=True)

    with panel(
        "Applied Skill Rules",
        "Rule traceability, execution status, and report readiness for this analysis",
        height=226,
        body_class="fs-overview-rules-panel",
    ):
        st.markdown('<div class="fs-overview-rule-strip"></div>', unsafe_allow_html=True)
        rule_cols = st.columns(5, gap="small")
        for column, record in zip(rule_cols, records[:5], strict=False):
            with column:
                rule_chip(
                    rule_id=str(record.get("rule_id", "RULE")),
                    title=str(record.get("step", "rule")),
                    status="Passed" if record.get("severity") != "WARNING" else "Review",
                    severity=str(record.get("severity", "INFO")),
                )

        st.markdown('<div class="fs-overview-rule-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="fs-overview-stat-row-spacer"></div>', unsafe_allow_html=True)

        footer_cols = st.columns([1.0, 1.0, 1.0, 1.18], gap="small")
        with footer_cols[0]:
            _overview_footer_stat(
                "Rules Executed",
                f"{len(records):,}",
                "Deduplicated audit records",
                "teal",
            )
        with footer_cols[1]:
            _overview_footer_stat(
                "Coverage",
                coverage_value,
                "Required Skill categories",
                "blue",
            )
        with footer_cols[2]:
            _overview_footer_stat(
                "Schema",
                schema_value,
                "Detected standardized schema",
                "purple",
            )
        with footer_cols[3]:
            if analysis_result is not None:
                html_report = build_html_report(analysis_result)
                st.download_button(
                    "Generate Report",
                    data=html_report.encode("utf-8"),
                    file_name="finskillos_analysis_report.html",
                    mime="text/html",
                    use_container_width=True,
                )
            else:
                st.markdown(
                    '<div class="fs-overview-report-unavailable">'
                    + status_badge("Report unavailable", "warning")
                    + "</div>",
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="fs-overview-footer-end"></div>', unsafe_allow_html=True)

def render_data_profile_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
    profile: dict[str, Any] | None,
    schema: dict[str, Any] | None,
) -> None:
    """Render the Data Profile detail tab as a flat card grid."""

    if df is None or profile is None:
        empty_state("Select a Dataset for Data Profiling", "Data quality, schema mapping, and sample preview appear here after analysis.")
        return

    missing_value, missing_caption = _missing_summary(profile)
    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Total Rows", f"{int(profile.get('row_count', 0)):,}", "Loaded rows", "teal", "#")
    with kpi_cols[1]:
        metric_card("Columns Detected", f"{int(profile.get('column_count', 0)):,}", "Auto-inferred", "blue", "[]")
    with kpi_cols[2]:
        metric_card("Date Range", _date_range(schema), "Standardized dates", "teal", "D")
    with kpi_cols[3]:
        metric_card("Missing Values", missing_value, missing_caption, "red" if missing_value != "0" else "teal", "!")
    with kpi_cols[4]:
        metric_card("Assets Detected", _asset_count(None, schema), "Unique assets", "purple", "A")
    with kpi_cols[5]:
        metric_card("Frequency", str(profile.get("frequency", "unknown")).title(), f"{profile.get('periods_per_year', 'N/A')} periods/year", "teal", "~")

    vspace(18)

    mapping_table = pd.DataFrame(schema.get("mapping_table", [])) if schema else pd.DataFrame()
    warnings = pd.DataFrame(profile.get("quality_warnings", []))
    numeric_columns = profile.get("numeric_columns", [])[:6]

    top_left, top_mid, top_right = st.columns([1.05, 1.1, 1.0])
    with top_left:
        with panel("Schema Mapping", "Raw columns mapped to FinSkillOS standard fields", height=392, scroll=True):
            if mapping_table.empty:
                empty_state("No Mapping Available", "No standard fields were mapped automatically.")
            else:
                mapping_cols = [col for col in ["field", "source", "confidence", "rule_id", "status"] if col in mapping_table.columns]
                compact_data_table(mapping_table.astype(str).to_dict("records"), columns=mapping_cols, max_rows=10)

    with top_mid:
        with panel("Data Quality", "Completeness and missing value overview", height=392, scroll=True):
            render_missing_values_chart(profile, height=230)
            if not warnings.empty:
                warning_cols = [col for col in ["rule_id", "severity", "message"] if col in warnings.columns]
                compact_data_table(warnings.astype(str).to_dict("records"), columns=warning_cols, max_rows=4)
            else:
                st.markdown(status_badge("No blocking quality warnings", "default"), unsafe_allow_html=True)

    with top_right:
        with panel("Rule Validation", "Applied data rules and validation status", height=392, scroll=True):
            _rule_validation_list_for_prefix(audit, {"DATA", "SCHEMA"}, limit=6)

    lower_left, lower_mid, lower_right = st.columns([1.05, 1.1, 1.0])
    with lower_left:
        with panel("Sample Data Preview", "First 10 rows from the loaded dataset", height=392, scroll=True):
            preview = df.head(10).astype(str)
            compact_data_table(preview.to_dict("records"), columns=list(preview.columns[:8]), max_rows=10)

    with lower_mid:
        with panel("Frequency & Coverage", "Rows observed through standardized time", height=392):
            render_frequency_coverage_chart(schema, height=315)

    with lower_right:
        with panel("Numeric Distributions", "Compact statistics for numeric columns", height=392, scroll=True):
            if not numeric_columns:
                empty_state("No Numeric Columns", "Distribution cards require numeric columns.")
            else:
                rows: list[dict[str, object]] = []
                for column in numeric_columns:
                    numeric = pd.to_numeric(df[column], errors="coerce").dropna()
                    if numeric.empty:
                        rows.append(
                            {
                                "column": str(column),
                                "mean": "N/A",
                                "min": "N/A",
                                "max": "N/A",
                                "n": "0",
                            }
                        )
                    else:
                        rows.append(
                            {
                                "column": str(column),
                                "mean": f"{numeric.mean():,.4g}",
                                "min": f"{numeric.min():,.4g}",
                                "max": f"{numeric.max():,.4g}",
                                "n": f"{len(numeric):,}",
                            }
                        )
                compact_data_table(rows, columns=["column", "mean", "min", "max", "n"], max_rows=6)

    st.markdown('<div class="fs-row-spacer fs-row-spacer-sm"></div>', unsafe_allow_html=True)


def render_return_analysis_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
    metrics: dict[str, Any] | None,
    insights: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> None:
    """Render the Return Analysis detail tab."""

    if not _require_analysis(df, metrics):
        return
    summary = metrics.get("summary", {})
    returns = metrics.get("returns")
    clean_returns = returns["return"].dropna() if isinstance(returns, pd.DataFrame) and "return" in returns.columns else pd.Series(dtype=float)
    best_period = clean_returns.max() if not clean_returns.empty else None
    worst_period = clean_returns.min() if not clean_returns.empty else None
    rolling_caption = f"{min(int(profile.get('periods_per_year', 252)) if profile else 63, 252)} period window"

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Total Return", format_percent(summary.get("total_return")), "Total over selected period", "teal", "TR")
    with kpi_cols[1]:
        metric_card("Annualized Return", format_percent(summary.get("annualized_return")), "Compounded per year", "teal", "AR")
    with kpi_cols[2]:
        metric_card("Best Period", format_percent(best_period), "Max observed return", "teal", "UP")
    with kpi_cols[3]:
        metric_card("Worst Period", format_percent(worst_period), "Min observed return", "red", "DN")
    with kpi_cols[4]:
        metric_card("Sharpe Ratio", format_ratio(summary.get("sharpe_ratio")), "Risk-adjusted return", "purple", "SR")
    with kpi_cols[5]:
        metric_card("Data Sufficiency", str(summary.get("data_sufficiency", "N/A")), "Observation quality", "blue", "DQ")

    vspace(18)

    top_left, top_right = st.columns([1.38, 1.0])
    with top_left:
        with panel("Cumulative Return", "Portfolio or asset indexed cumulative return", height=380):
            render_cumulative_return_chart(metrics, height=300)
    with top_right:
        with panel("Return Insights", None, height=380, scroll=True):
            vspace(14)
            items = [item for item in (insights or {}).get("insights", []) if item.get("category") in {"return", "sharpe", "data_quality"}]
            if not items:
                empty_state("No Return Insights", "No return-specific insight was generated.")
            for item in items[:3]:
                insight_card(
                    category=str(item.get("category", "return")),
                    fact=str(item.get("fact", "")),
                    interpretation=str(item.get("interpretation", "")),
                    caution=str(item.get("caution", "")),
                    severity=str(item.get("severity", "INFO")),
                    compact=True,
                )
                vspace(14)

    bottom_left, bottom_mid, bottom_right = st.columns([1.0, 1.0, 1.0])
    with bottom_left:
        with panel("Monthly Returns Heatmap", "Portfolio average returns aggregated by month", height=326):
            render_monthly_returns_heatmap(metrics, height=245)
    with bottom_mid:
        with panel("Return Distribution", "Period return histogram", height=326):
            render_return_distribution(metrics, height=245)
    with bottom_right:
        with panel("Rolling Return", rolling_caption, height=326):
            render_rolling_return_chart(metrics, window=min(int(profile.get("periods_per_year", 63)) if profile else 63, 252), height=245)

    with panel("Period Return Summary", None, scroll=True):
        asset_metrics = pd.DataFrame(metrics.get("asset_metrics", []))
        if asset_metrics.empty:
            empty_state("Metric Table Unavailable", "Asset-level metrics were not generated for this dataset.")
        else:
            display_cols = [col for col in ["asset", "total_return", "annualized_return", "annualized_volatility", "sharpe_ratio"] if col in asset_metrics.columns]
            formatted = _format_metric_table(
                asset_metrics[display_cols],
                percent_cols={"total_return", "annualized_return", "annualized_volatility"},
                ratio_cols={"sharpe_ratio"},
            )
            compact_data_table(formatted.to_dict("records"), columns=display_cols, max_rows=8)

    with panel("Applied Return Rules", "Rule traceability and execution status for this analysis", scroll=True):
        _rule_validation_list_for_prefix(audit, {"METRIC", "VIS"}, limit=5)


def render_risk_analysis_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
    metrics: dict[str, Any] | None,
    insights: dict[str, Any] | None,
    profile: dict[str, Any] | None,
) -> None:
    """Render the Risk Analysis detail tab."""

    if not _require_analysis(df, metrics):
        return
    summary = metrics.get("summary", {})
    periods = int(profile.get("periods_per_year", 252)) if profile else 252

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Volatility (Ann.)", format_percent(summary.get("annualized_volatility")), "Standard deviation", "blue", "VOL")
    with kpi_cols[1]:
        metric_card("Max Drawdown", format_percent(summary.get("max_drawdown")), "From peak to trough", "red", "MDD")
    with kpi_cols[2]:
        metric_card("VaR (95%)", format_percent(summary.get("historical_var_95")), "Historical approximation", "purple", "VAR")
    with kpi_cols[3]:
        metric_card("VaR (99%)", format_percent(summary.get("historical_var_99")), "Historical approximation", "purple", "V99")
    with kpi_cols[4]:
        metric_card("Downside Deviation", format_percent(summary.get("downside_deviation")), "Below zero return", "amber", "DD")
    with kpi_cols[5]:
        metric_card("Risk Level", str(summary.get("risk_level", "UNKNOWN")), "Rule-based classification", "amber", "RL")

    vspace(18)

    top_left, top_mid, top_right = st.columns([1.2, 1.05, 0.82])
    with top_left:
        with panel("Underwater Drawdown", "Cumulative drawdown through time", height=365, body_class="fs-panel-lean"):
            render_drawdown_chart(metrics, height=285)
    with top_mid:
        with panel("Rolling Volatility", "Annualized rolling volatility", height=365, body_class="fs-panel-lean"):
            render_rolling_volatility_chart(metrics, periods_per_year=periods, window=min(periods, 252), height=285)
    with top_right:
        with panel("Risk Commentary", None, height=365, scroll=True, body_class="fs-panel-lean"):
            vspace(20)
            items = [item for item in (insights or {}).get("insights", []) if item.get("category") in {"drawdown", "volatility", "data_quality"}]
            if not items:
                empty_state("No Risk Insights", "No risk-specific insight was generated.")
            for item in items[:3]:
                insight_card(
                    category=str(item.get("category", "risk")),
                    fact=str(item.get("fact", "")),
                    interpretation=str(item.get("interpretation", "")),
                    caution=str(item.get("caution", "")),
                    severity=str(item.get("severity", "INFO")),
                    compact=True,
                )
                vspace(14)

    lower_left, lower_mid, lower_right = st.columns([1.0, 1.0, 1.0])
    with lower_left:
        with panel("VaR / CVaR Distribution", "Historical returns with tail-risk reference lines", height=324, body_class="fs-panel-lean"):
            render_var_cvar_distribution(metrics, height=245)
    with lower_mid:
        with panel("Stress Scenario Impact", None, height=324, scroll=True, body_class="fs-panel-lean"):
            vspace(14)
            stress = pd.DataFrame(
                [
                    {"scenario": "Observed worst period", "impact": format_percent(summary.get("max_drawdown")), "severity": summary.get("drawdown_risk_level", "UNKNOWN")},
                    {"scenario": "Volatility regime", "impact": format_percent(summary.get("annualized_volatility")), "severity": summary.get("volatility_risk_level", "UNKNOWN")},
                    {"scenario": "Data sufficiency", "impact": str(summary.get("data_sufficiency", "N/A")), "severity": "INFO"},
                ]
            )
            compact_data_table(stress.astype(str).to_dict("records"), columns=["scenario", "impact", "severity"], max_rows=5)
    with lower_right:
        with panel("Data Profile & Assumptions", None, height=324, scroll=True, body_class="fs-panel-lean"):
            vspace(14)
            assumptions = [
                {"item": "Return Frequency", "value": str(profile.get("frequency", "unknown")).title() if profile else "N/A"},
                {"item": "Periods / Year", "value": periods},
                {"item": "Observation Count", "value": summary.get("observation_count", "N/A")},
                {"item": "Risk-Free Rate", "value": format_percent(summary.get("risk_free_rate"))},
            ]
            key_value_table(assumptions)

    with panel("Applied Risk Rules", "Rule traceability and execution status for this analysis", scroll=True):
        _rule_validation_list_for_prefix(audit, {"RISK", "METRIC", "SAFE"}, limit=5)


def render_diversification_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
    schema: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    insights: dict[str, Any] | None,
) -> None:
    """Render the Diversification tab with available cards promoted first."""

    if not _require_analysis(df, metrics):
        return

    summary = metrics.get("summary", {}) if metrics else {}
    avg_corr = _average_correlation(metrics)
    allocation_rows = _allocation_rows(schema)
    asset_metrics = pd.DataFrame(metrics.get("asset_metrics", [])) if metrics else pd.DataFrame()
    corr = metrics.get("correlation_matrix") if metrics else None

    diversification_items = [
        item
        for item in (insights or {}).get("insights", [])
        if item.get("category") in {"correlation", "diversification", "allocation", "concentration", "data_quality"}
    ]

    correlation_available = isinstance(corr, pd.DataFrame) and not corr.empty and corr.shape[0] >= 2
    allocation_available = not allocation_rows.empty
    insights_available = len(diversification_items) > 0

    risk_contribution_available = (
        not asset_metrics.empty
        and {"asset", "annualized_volatility"}.issubset(asset_metrics.columns)
        and pd.to_numeric(asset_metrics["annualized_volatility"], errors="coerce").dropna().sum() > 0
    )
    risk_return_available = (
        not asset_metrics.empty
        and {"asset", "annualized_volatility", "annualized_return"}.issubset(asset_metrics.columns)
        and not asset_metrics.dropna(subset=["annualized_volatility", "annualized_return"]).empty
    )
    concentration_available = allocation_available

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card(
            "Average Correlation",
            f"{avg_corr:.2f}" if avg_corr is not None else "N/A",
            "Off-diagonal mean",
            "blue",
            "ρ",
        )
    with kpi_cols[1]:
        metric_card(
            "Asset Count",
            _asset_count(metrics, schema),
            "Distinct assets",
            "teal",
            "A",
        )
    with kpi_cols[2]:
        largest_weight, largest_asset = _largest_weight(schema)
        metric_card(
            "Largest Weight",
            largest_weight,
            largest_asset,
            "amber" if largest_weight != "N/A" else "blue",
            "W",
        )
    with kpi_cols[3]:
        metric_card(
            "Cash Exposure",
            _cash_exposure(schema),
            "Detected cash allocation",
            "teal",
            "$",
        )
    with kpi_cols[4]:
        metric_card(
            "Diversification",
            str(summary.get("diversification_level", summary.get("risk_level", "N/A"))),
            "Rule-based signal",
            "purple",
            "D",
        )
    with kpi_cols[5]:
        metric_card(
            "Warnings",
            str(len([record for record in audit.deduplicated_records() if record.get("severity") == "WARNING"])),
            "Audit warnings",
            "red",
            "!",
        )

    vspace(18)

    def _render_correlation() -> None:
        with panel("Correlation Heatmap", "Pearson correlation across asset returns", height=392):
            render_correlation_heatmap(metrics, height=315)

    def _render_allocation() -> None:
        with panel("Portfolio Allocation", "Weight-based exposure when available", height=392):
            render_allocation_chart(schema, height=315)

    def _render_insights() -> None:
        with panel("Diversification Insights", "Available insight cards are promoted ahead of unavailable panels", height=392, scroll=True):
            if not diversification_items:
                empty_state("No Diversification Insights", "No diversification-specific insights were generated.")
                return
            for item in diversification_items[:4]:
                insight_card(
                    category=str(item.get("category", "Diversification")),
                    fact=str(item.get("fact", "")),
                    interpretation=str(item.get("interpretation", "")),
                    caution=str(item.get("caution", "")),
                    severity=str(item.get("severity", "INFO")),
                    compact=True,
                )
                vspace(12)

    def _render_risk_contribution() -> None:
        with panel("Risk Contribution", "Volatility-weighted asset contribution proxy", height=392):
            render_risk_contribution_chart(metrics, height=315)

    def _render_risk_return() -> None:
        with panel("Risk vs. Return", "Asset comparison", height=392):
            render_risk_return_scatter(metrics, height=315)

    def _render_concentration() -> None:
        with panel("Concentration Analysis", "Weight concentration and exposure summary", height=392, scroll=True):
            if allocation_rows.empty:
                empty_state("Concentration Unavailable", "Concentration metrics require an allocation weight column.")
                return

            working = allocation_rows.copy()
            working["weight"] = pd.to_numeric(working["weight"], errors="coerce")
            working = working.dropna(subset=["asset", "weight"])
            if working.empty:
                empty_state("Concentration Unavailable", "No valid asset weights were available.")
                return

            total_weight = float(working["weight"].sum())
            top_weight = float(working["weight"].max())
            top_asset = str(working.loc[working["weight"].idxmax(), "asset"])
            hhi = float((working["weight"] ** 2).sum())
            top3 = float(working.sort_values("weight", ascending=False).head(3)["weight"].sum())

            rows = [
                {"item": "Largest Asset", "value": top_asset},
                {"item": "Largest Weight", "value": format_percent(top_weight)},
                {"item": "Top 3 Weight", "value": format_percent(top3)},
                {"item": "Weight Sum", "value": format_percent(total_weight)},
                {"item": "HHI Proxy", "value": f"{hhi:.3f}"},
            ]
            key_value_table(rows)

    card_specs = [
        {
            "title": "Correlation Heatmap",
            "available": correlation_available,
            "render": _render_correlation,
        },
        {
            "title": "Portfolio Allocation",
            "available": allocation_available,
            "render": _render_allocation,
        },
        {
            "title": "Diversification Insights",
            "available": insights_available,
            "render": _render_insights,
        },
        {
            "title": "Risk Contribution",
            "available": risk_contribution_available,
            "render": _render_risk_contribution,
        },
        {
            "title": "Risk vs. Return",
            "available": risk_return_available,
            "render": _render_risk_return,
        },
        {
            "title": "Concentration Analysis",
            "available": concentration_available,
            "render": _render_concentration,
        },
    ]

    ordered_cards = [card for card in card_specs if card["available"]] + [card for card in card_specs if not card["available"]]

    for row_start in range(0, len(ordered_cards), 3):
        row_cards = ordered_cards[row_start : row_start + 3]
        columns = st.columns(3)
        for column, card in zip(columns, row_cards, strict=False):
            with column:
                card["render"]()
        if row_start + 3 < len(ordered_cards):
            vspace(8)

    with panel("Applied Diversification Rules", "Rule traceability and execution status for this analysis", height=300, scroll=True):
        _rule_validation_list_for_prefix(audit, {"METRIC", "VIS", "RISK", "SAFE"}, limit=6)



def render_insights_tab(
    df: pd.DataFrame | None,
    source_name: str,
    audit: RuleAuditLog,
    schema: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    insights: dict[str, Any] | None,
) -> None:
    """Render the evidence-traced Insights tab."""

    if not _analysis_available(df):
        return
    items = list((insights or {}).get("insights", []))
    summary = metrics.get("summary", {}) if metrics else {}
    selected_index, selected = _selected_insight(items)

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        metric_card("Insights", f"{len(items):,}", "Evidence-linked cards", "teal", "IN")
    with kpi_cols[1]:
        metric_card("Total Return", format_percent(summary.get("total_return")), "Cumulative", "teal", "TR")
    with kpi_cols[2]:
        metric_card("Volatility", format_percent(summary.get("annualized_volatility")), "Annualized", "blue", "VO")
    with kpi_cols[3]:
        metric_card("Max Drawdown", format_percent(summary.get("max_drawdown")), "From peak to trough", "red", "MD")
    with kpi_cols[4]:
        metric_card("Risk Level", str(summary.get("risk_level", "UNKNOWN")), "Rule-classified", "amber", "RL")

    vspace(18)

    st.markdown("### Executive Insight Summary")
    with panel("Executive Insight Summary", "Generated and validated via Skills.md rules.", scroll=True):
        if items:
            lead = items[0]
            st.markdown(
                f"Across `{source_name}`, FinSkillOS generated **{len(items)}** evidence-linked insight(s). "
                f"The lead signal is **{lead.get('category', 'insight')}** with severity **{lead.get('severity', 'INFO')}**."
            )
            
        else:
            empty_state("No Insights Generated", "The insight engine did not produce evidence-linked insight cards for this dataset.")
        vspace(14)

    feed_col, detail_col, trace_col = st.columns([0.92, 1.35, 0.86])
    with feed_col:
        with panel("Insight Feed", None, height=720, scroll=True):
            if not items:
                empty_state("Empty Feed", "No insight cards are available.")
            for idx, item in enumerate(items):
                insight_card(
                    category=str(item.get("category", "Insight")),
                    fact=str(item.get("fact", "")),
                    interpretation=str(item.get("interpretation", "")),
                    caution=str(item.get("caution", "")),
                    severity=str(item.get("severity", "INFO")),
                    selected=idx == selected_index,
                )
                vspace(12)

    with detail_col:
        with panel("Selected Insight", None, height=720, scroll=True):
            vspace(20)
            if selected is None:
                empty_state("No Selection", "Select an insight from the feed to inspect its evidence.")
            else:
                insight_card(
                    category=str(selected.get("category", "Insight")),
                    fact=str(selected.get("fact", "")),
                    interpretation=str(selected.get("interpretation", "")),
                    caution=str(selected.get("caution", "")),
                    severity=str(selected.get("severity", "INFO")),
                    selected=True,
                )
                st.markdown("##### Supporting Visualization")
                evidence = selected.get("evidence", {})
                chart_name = str(evidence.get("chart", ""))
                if "drawdown" in chart_name:
                    render_drawdown_chart(metrics, height=285)
                elif "correlation" in chart_name:
                    render_correlation_heatmap(metrics, height=285)
                else:
                    render_cumulative_return_chart(metrics, height=285)

                evidence_rows = pd.DataFrame(
                    [{"field": key, "value": value} for key, value in dict(evidence).items()]
                )
                st.markdown("##### Evidence Sources")
                if evidence_rows.empty:
                    empty_state("No Evidence Rows", "This insight did not expose structured evidence.")
                else:
                    key_value_table(evidence_rows.rename(columns={"field": "item"}).astype(str).to_dict("records"))

    with trace_col:
        with panel("Insight Validation & Traceability", None, height=720, scroll=True):
            records = _rule_records(audit)
            if selected is None:
                empty_state("No Traceability", "Select an insight to inspect its referenced rules.")
            else:
                rule_ids = [str(rule_id) for rule_id in selected.get("rule_ids", [])]
                st.markdown("##### Rules Applied")
                rules_df = _rule_reference_rows(rule_ids, records)
                if rules_df.empty:
                    empty_state("No Rule References", "No rule IDs were attached to this insight.")
                else:
                    rule_cols = [col for col in ["rule_id", "severity", "step", "result"] if col in rules_df.columns]
                    compact_data_table(rules_df.astype(str).to_dict("records"), columns=rule_cols, max_rows=5)
                st.markdown("##### Data Source")
                key_value_table(
                    [
                        {"item": "Dataset", "value": source_name},
                        {"item": "Schema", "value": schema.get("schema_type", "unknown") if schema else "unknown"},
                        {"item": "Date Range", "value": _date_range(schema)},
                    ]
                )
                st.markdown(status_badge("Generated and validated via Skills.md rules", "default"), unsafe_allow_html=True)

    st.markdown("### Pinned Insights & Next Steps")
    next_cols = st.columns(4)
    next_steps = [
        ("Monitor Drawdown Regimes", "Linked to max drawdown and underwater chart."),
        ("Assess Volatility Drivers", "Linked to rolling volatility and asset metrics."),
        ("Review Diversification", "Linked to correlation and risk-return scatter."),
        ("Validate Data Inputs", "Linked to Data Profile quality warnings."),
    ]
    for column, (title, description) in zip(next_cols, next_steps, strict=False):
        with column:
            rule_card("NEXT", title, description, status="Queued", severity="INFO")
    vspace(14)
    st.markdown('<div class="fs-insights-footer-end"></div>', unsafe_allow_html=True)

def render_applied_rules_tab(df: pd.DataFrame | None, audit: RuleAuditLog) -> None:
    """Render the Applied Rules governance tab."""

    if not _analysis_available(df):
        return
    records = _rule_records(audit)
    summary = _rule_summary(records)
    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Rules Executed", f"{summary['executed']:,}", "Total rules run", "blue", "RU")
    with kpi_cols[1]:
        metric_card("Passed", f"{summary['passed']:,}", "No warning flag", "teal", "OK")
    with kpi_cols[2]:
        metric_card("Warnings", f"{summary['warnings']:,}", "Review recommended", "amber", "WR")
    with kpi_cols[3]:
        metric_card("Blocked", f"{summary['blocked']:,}", "Hard failures", "red", "BL")
    with kpi_cols[4]:
        metric_card("Coverage", f"{summary['coverage']}/{summary['required']}", "Required categories", "purple", "CV")
    with kpi_cols[5]:
        metric_card("Avg Execution", "local", "In-process rules", "blue", "TM")

    vspace(18)

    table_col, timeline_col, graph_col, side_col = st.columns([1.35, 0.78, 0.9, 0.82])
    with table_col:
        with panel("Rules Table", None, height=520, scroll=True):
            search = st.text_input("Search rules", placeholder="Search by rule ID, prefix, step, or result...", label_visibility="collapsed")
            rules_df = pd.DataFrame(records)
            if search and not rules_df.empty:
                mask = rules_df.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
                rules_df = rules_df[mask]
            if rules_df.empty:
                empty_state("No Rules Found", "No applied rules match the current search.")
            else:
                display_cols = [col for col in ["order", "rule_id", "prefix", "step", "severity", "result"] if col in rules_df.columns]
                compact_data_table(rules_df[display_cols].astype(str).to_dict("records"), columns=display_cols, max_rows=12)

    with timeline_col:
        with panel("Execution Timeline", None, height=520, scroll=True):
            timeline = pd.DataFrame(
                [
                    {
                        "time": f"T+{idx:02d}",
                        "rule": record.get("rule_id"),
                        "status": "warning" if record.get("severity") == "WARNING" else "passed",
                    }
                    for idx, record in enumerate(records[:10], start=1)
                ]
            )
            if timeline.empty:
                empty_state("No Timeline", "No rules were executed.")
            else:
                compact_data_table(timeline.astype(str).to_dict("records"), columns=["time", "rule", "status"], max_rows=10)
            st.markdown(status_badge("Live trace", "default"), unsafe_allow_html=True)
            vspace(8)

    with graph_col:
        with panel("Rule Dependency Graph", "Hard and soft dependencies are represented by rule domains in this MVP.", height=520, scroll=True):
            dependency = pd.DataFrame(
                [
                    {"domain": "Data Quality", "rules": sum(1 for row in records if row.get("prefix") in {"DATA", "SCHEMA"})},
                    {"domain": "Metrics", "rules": sum(1 for row in records if row.get("prefix") in {"METRIC", "RISK"})},
                    {"domain": "Visualization", "rules": sum(1 for row in records if row.get("prefix") == "VIS")},
                    {"domain": "Safety", "rules": sum(1 for row in records if row.get("prefix") in {"INSIGHT", "SAFE"})},
                ]
            )
            compact_data_table(dependency.astype(str).to_dict("records"), columns=["domain", "rules"], max_rows=4)

    with side_col:
        with panel("Governance Overview", None, height=520, scroll=True):
            grade = "A+" if summary["blocked"] == 0 and summary["coverage"] >= 5 else "Review"
            st.metric("System Integrity", grade)
            key_value_table(
                [
                    {"item": "Rule Coverage", "value": f"{summary['coverage']}/{summary['required']}"},
                    {"item": "Warnings", "value": summary["warnings"]},
                    {"item": "Blocked", "value": summary["blocked"]},
                    {"item": "Loaded From", "value": "Skills.md"},
                ]
            )

    with panel("Representative Rule Validation", "Readable execution rows for core rule domains", scroll=True):
        _rule_validation_list_for_prefix(audit, {"DATA", "SCHEMA", "METRIC", "VIS", "RISK", "INSIGHT", "SAFE"}, limit=6)

    st.markdown("### Exceptions")
    exceptions = [record for record in records if record.get("severity") == "WARNING"]
    if not exceptions:
        st.markdown(status_badge("No warnings or blocked rules", "default"), unsafe_allow_html=True)
    else:
        exception_df = pd.DataFrame(exceptions)
        exception_cols = [col for col in ["rule_id", "prefix", "severity", "step", "result"] if col in exception_df.columns]
        compact_data_table(exception_df.astype(str).to_dict("records"), columns=exception_cols, max_rows=8)


def render_reports_tab(
    df: pd.DataFrame | None,
    source_name: str,
    audit: RuleAuditLog,
    profile: dict[str, Any] | None,
    schema: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    analysis_result: dict[str, Any] | None,
) -> None:
    """Render the Reports workspace tab."""

    if not _analysis_available(df):
        return
    records = _rule_records(audit)
    summary = _rule_summary(records)
    html_report = build_html_report(analysis_result) if analysis_result is not None else ""

    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        metric_card("Reports Generated", "1", "Current analysis", "teal", "RP")
    with kpi_cols[1]:
        metric_card("Latest Version", "v2.0", "Skills.md governed", "blue", "V")
    with kpi_cols[2]:
        metric_card("Export Formats", "3", "HTML, CSV, JSON", "purple", "EX")
    with kpi_cols[3]:
        metric_card("Rules Included", f"{len(records):,}", "Audit trail", "teal", "RU")
    with kpi_cols[4]:
        metric_card("Data Rows", f"{int(profile.get('row_count', 0)):,}" if profile else "N/A", "Profile summary", "blue", "DR")
    with kpi_cols[5]:
        metric_card("Delivery Status", "Healthy", "Local export ready", "teal", "OK")

    vspace(18)

    library_col, preview_col, action_col, summary_col = st.columns([1.0, 1.25, 0.82, 0.9])
    with library_col:
        with panel("Report Library", None, height=700, scroll=True):
            vspace(8)
            compact_data_table(_report_library(source_name).astype(str).to_dict("records"), max_rows=8)

    with preview_col:
        with panel("Report Preview", None, height=700, scroll=True):
            vspace(8)
            if not html_report:
                empty_state("Preview Unavailable", "Report preview requires an analysis result.")
            else:
                preview_summary = pd.DataFrame(
                    [
                        {"section": "Dataset Summary", "status": "Included"},
                        {"section": "Schema Mapping", "status": "Included"},
                        {"section": "Metric Summary", "status": "Included"},
                        {"section": "Risk Insights", "status": "Included"},
                        {"section": "Applied Rules", "status": f"{len(records)} rows"},
                        {"section": "Disclaimer", "status": "Included"},
                    ]
                )
                compact_data_table(preview_summary.astype(str).to_dict("records"), columns=["section", "status"], max_rows=8)
                st.caption(f"Preview bytes: {len(html_report.encode('utf-8')):,}")

    with action_col:
        with panel("Export & Share", "Available now vs planned next", height=700, scroll=True):
            st.markdown("#### Available Exports")
            available_exports = [
                {"format": "HTML Report", "status": "Available"},
                {"format": "Rules CSV", "status": "Available"},
                {"format": "Rules JSON", "status": "Available"},
            ]
            compact_data_table(available_exports, columns=["format", "status"], max_rows=3)
            if html_report:
                st.download_button(
                    "Download HTML Report",
                    data=html_report.encode("utf-8"),
                    file_name="finskillos_analysis_report.html",
                    mime="text/html",
                    use_container_width=True,
                )
            rules_df = pd.DataFrame(records)
            st.download_button(
                "Download Rules CSV",
                data=rules_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="finskillos_applied_rules.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.download_button(
                "Download Rules JSON",
                data=json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name="finskillos_applied_rules.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown("#### Planned Extensions")
            planned_exports = [
                {"format": "PDF Export", "status": "Planned"},
                {"format": "PPTX Export", "status": "Planned"},
                {"format": "Secure Share Link", "status": "Planned"},
                {"format": "Scheduled Delivery", "status": "Planned"},
            ]
            compact_data_table(planned_exports, columns=["format", "status"], max_rows=4)

    with summary_col:
        with panel("Report Summary", None, height=700, scroll=True):
            vspace(8)
            includes = pd.DataFrame(
                [
                    {"item": "Executive summary with key metrics", "status": "Included"},
                    {"item": "Risk and return analysis", "status": "Included"},
                    {"item": "Schema and data profile", "status": "Included"},
                    {"item": "Rule audit trail", "status": "Included"},
                    {"item": "Safety disclaimer", "status": "Included"},
                ]
            )
            compact_data_table(includes.astype(str).to_dict("records"), columns=["item", "status"], max_rows=6)
            st.markdown("#### Validation Status")
            key_value_table(
                [
                    {"item": "Rule Coverage", "value": f"{summary['coverage']}/{summary['required']}"},
                    {"item": "Warnings", "value": summary["warnings"]},
                    {"item": "Blocked", "value": summary["blocked"]},
                    {"item": "Schema", "value": schema.get("schema_type", "unknown") if schema else "unknown"},
                ]
            )

    with panel("Report Rules & Validation", "Rules included in the current export package", scroll=True):
        _rule_validation_list_for_prefix(audit, {"METRIC", "RISK", "INSIGHT", "SAFE", "AUTO"}, limit=5)

# ---------------------------------------------------------------------------
# Layout override: Reports tab v8
# Appended by apply_reports_layout_v8.py.
# This later definition intentionally overrides the earlier render_reports_tab.
# ---------------------------------------------------------------------------
def render_reports_tab(
    df: pd.DataFrame | None,
    source_name: str,
    audit: RuleAuditLog,
    profile: dict[str, Any] | None,
    schema: dict[str, Any] | None,
    metrics: dict[str, Any] | None,
    analysis_result: dict[str, Any] | None,
) -> None:
    """Render the Reports tab with action-first, balanced card layout."""

    if not _analysis_available(df):
        return

    records = _rule_records(audit)
    rule_summary = _rule_summary(records)
    schema_name = str(schema.get("schema_type", "unknown") if schema else "unknown")
    row_count = int(profile.get("row_count", 0)) if profile else 0
    asset_count = _asset_count(metrics, schema)
    html_report = build_html_report(analysis_result) if analysis_result is not None else ""
    html_bytes = html_report.encode("utf-8") if html_report else b""
    rules_df = pd.DataFrame(records)
    rules_csv = rules_df.to_csv(index=False).encode("utf-8") if not rules_df.empty else b""
    rules_json = json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")

    summary = metrics.get("summary", {}) if metrics else {}
    report_library = _report_library(source_name)

    preview_rows = [
        {"section": "Dataset Summary", "status": "Included"},
        {"section": "Schema Mapping", "status": "Included" if schema else "Unavailable"},
        {"section": "Metric Summary", "status": "Included" if metrics else "Unavailable"},
        {"section": "Risk Insights", "status": "Included" if analysis_result else "Unavailable"},
        {"section": "Applied Rules", "status": f"{len(records):,} rows"},
        {"section": "Disclaimer", "status": "Included"},
    ]

    export_rows = [
        {"format": "HTML Report", "status": "Available" if html_bytes else "Unavailable"},
        {"format": "Rules CSV", "status": "Available" if rules_csv else "Unavailable"},
        {"format": "Rules JSON", "status": "Available"},
    ]

    planned_rows = [
        {"format": "PDF Export", "status": "Planned"},
        {"format": "PPTX Export", "status": "Planned"},
        {"format": "Secure Share Link", "status": "Planned"},
        {"format": "Scheduled Delivery", "status": "Planned"},
    ]

    report_summary_rows = [
        {"item": "Dataset", "value": source_name},
        {"item": "Schema", "value": schema_name},
        {"item": "Rows", "value": f"{row_count:,}" if row_count else "N/A"},
        {"item": "Assets", "value": asset_count},
        {"item": "Total Return", "value": format_percent(summary.get("total_return")) if summary else "N/A"},
        {"item": "Risk Level", "value": str(summary.get("risk_level", "N/A"))},
    ]

    validation_rows = [
        {"item": "Rule Coverage", "value": f"{rule_summary['coverage']}/{rule_summary['required']}"},
        {"item": "Rules Executed", "value": f"{rule_summary['executed']:,}"},
        {"item": "Warnings", "value": f"{rule_summary['warnings']:,}"},
        {"item": "Blocked", "value": f"{rule_summary['blocked']:,}"},
        {"item": "Loaded From", "value": "Skills.md"},
    ]

    primary_left, primary_mid, primary_right = st.columns([1.35, 0.95, 0.92])
    with primary_left:
        with panel("Report Preview", "Current export package contents", height=396, scroll=True):
            compact_data_table(preview_rows, columns=["section", "status"], max_rows=8)
            st.caption(f"Preview bytes: {len(html_bytes):,}" if html_bytes else "Preview unavailable until analysis is available.")

    with primary_mid:
        with panel("Export & Share", "Available now vs planned next", height=396, scroll=True):
            st.markdown("#### Available Exports")
            compact_data_table(export_rows, columns=["format", "status"], max_rows=5)
            st.download_button(
                "Download HTML Report",
                data=html_bytes,
                file_name="finskillos_analysis_report.html",
                mime="text/html",
                use_container_width=True,
                disabled=not bool(html_bytes),
            )
            st.download_button(
                "Download Rules CSV",
                data=rules_csv,
                file_name="finskillos_rule_audit.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=not bool(rules_csv),
            )
            st.download_button(
                "Download Rules JSON",
                data=rules_json,
                file_name="finskillos_rule_audit.json",
                mime="application/json",
                use_container_width=True,
                disabled=not bool(records),
            )

    with primary_right:
        with panel("Report Summary", "Dataset, schema, and output status", height=396, scroll=True):
            key_value_table(report_summary_rows, key_label="Item", value_label="Status")
            vspace(10)
            st.markdown("#### Validation Status")
            key_value_table(validation_rows)

    vspace(10)

    secondary_left, secondary_mid, secondary_right = st.columns([1.05, 0.95, 1.35])
    with secondary_left:
        with panel("Report Library", "Generated report artifacts for the current dataset", height=340, scroll=True):
            compact_data_table(report_library.astype(str).to_dict("records"), columns=list(report_library.columns), max_rows=8)

    with secondary_mid:
        with panel("Planned Extensions", "Future export and delivery options", height=340, scroll=True):
            compact_data_table(planned_rows, columns=["format", "status"], max_rows=8)

    with secondary_right:
        with panel("Report Rules & Validation", "Rules included in the current export package", height=340, scroll=True):
            if not records:
                empty_state("No Rules Available", "Rule audit records will appear after analysis.")
            else:
                rule_validation_list(records, limit=6)

    st.markdown('<div class="fs-row-spacer fs-row-spacer-sm"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Layout override: Applied Rules tab v11
# Appended by apply_applied_rules_layout_v11.py.
# This later definition intentionally overrides the earlier render_applied_rules_tab.
# ---------------------------------------------------------------------------
def render_applied_rules_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
) -> None:
    """Render the Applied Rules tab as a full audit browser.

    v11 fixes the main usability issue: Rules Executed can be 45+ while the
    visible table was capped by max_rows. The rules table now renders all
    filtered rows inside a local scroll panel.
    """

    if not _analysis_available(df):
        return

    records = _rule_records(audit)
    summary = _rule_summary(records)

    if not records:
        empty_state("No Applied Rules", "Rule audit records will appear after analysis.")
        return

    rules_df = pd.DataFrame(records).copy()
    preferred_cols = ["rule_id", "prefix", "step", "severity", "result"]
    available_cols = [col for col in preferred_cols if col in rules_df.columns]
    rules_df = rules_df[available_cols].copy()

    rules_df.insert(0, "order", range(1, len(rules_df) + 1))
    rules_df["status"] = rules_df["severity"].map(
        lambda value: "review" if str(value).upper() == "WARNING" else "blocked" if str(value).upper() == "ERROR" else "passed"
    )

    search = st.text_input(
        "Search rules",
        placeholder="Search by rule ID, prefix, step, severity, or result...",
        label_visibility="collapsed",
        key="applied_rules_search_v11",
    ).strip()

    filtered_df = rules_df
    if search:
        mask = rules_df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered_df = rules_df[mask].copy()

    warnings = int((rules_df["severity"].astype(str).str.upper() == "WARNING").sum()) if "severity" in rules_df.columns else 0
    blocked = int((rules_df["severity"].astype(str).str.upper() == "ERROR").sum()) if "severity" in rules_df.columns else 0
    passed = max(len(rules_df) - warnings - blocked, 0)

    top_cols = st.columns(5)
    with top_cols[0]:
        metric_card("Rules Executed", f"{len(records):,}", "Deduplicated audit records", "teal", "#")
    with top_cols[1]:
        metric_card("Visible Rows", f"{len(filtered_df):,}", "After search filter", "blue", "F")
    with top_cols[2]:
        metric_card("Coverage", f"{summary['coverage']}/{summary['required']}", "Required Skill categories", "purple", "C")
    with top_cols[3]:
        metric_card("Warnings", f"{warnings:,}", "Review-level records", "amber" if warnings else "teal", "!")
    with top_cols[4]:
        metric_card("Blocked", f"{blocked:,}", "Error-level records", "red" if blocked else "teal", "X")

    vspace(16)

    left, right = st.columns([1.72, 1.0])
    with left:
        with panel(
            "Rules Table",
            f"Showing {len(filtered_df):,} of {len(rules_df):,} executed rule records",
            height=560,
            scroll=True,
        ):
            if filtered_df.empty:
                empty_state("No Matching Rules", "No rule audit records matched the current search.")
            else:
                display_cols = ["order", "rule_id", "prefix", "step", "severity", "status", "result"]
                display_cols = [col for col in display_cols if col in filtered_df.columns]
                compact_data_table(
                    filtered_df.astype(str).to_dict("records"),
                    columns=display_cols,
                    max_rows=len(filtered_df),
                )

    with right:
        with panel("Governance Overview", "Coverage, severity, and source status", height=260, scroll=True):
            integrity_grade = "A+" if blocked == 0 and summary["coverage"] == summary["required"] else "A" if blocked == 0 else "Review"
            st.markdown(
                f"""
                <div class="fs-governance-grade">
                  <div class="fs-governance-grade-label">System Integrity</div>
                  <div class="fs-governance-grade-value">{integrity_grade}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            rows = [
                {"item": "Rule Coverage", "value": f"{summary['coverage']}/{summary['required']}"},
                {"item": "Rules Executed", "value": f"{summary['executed']:,}"},
                {"item": "Passed", "value": f"{passed:,}"},
                {"item": "Warnings", "value": f"{warnings:,}"},
                {"item": "Blocked", "value": f"{blocked:,}"},
                {"item": "Loaded From", "value": "Skills.md"},
            ]
            key_value_table(rows)

        vspace(12)

        with panel("Rule Domains", "Executed records grouped by rule prefix", height=288, scroll=True):
            if "prefix" not in rules_df.columns:
                empty_state("No Prefix Data", "Rule prefix metadata is unavailable.")
            else:
                domain_rows = (
                    rules_df.groupby("prefix", dropna=False)
                    .size()
                    .reset_index(name="rules")
                    .sort_values("rules", ascending=False)
                )
                compact_data_table(
                    domain_rows.astype(str).to_dict("records"),
                    columns=["prefix", "rules"],
                    max_rows=len(domain_rows),
                )

    vspace(10)

    lower_left, lower_mid, lower_right = st.columns([1.05, 1.0, 1.25])
    with lower_left:
        with panel("Execution Timeline", "First-to-last audit execution order", height=360, scroll=True):
            timeline_df = filtered_df[["order", "rule_id", "status"]].copy() if not filtered_df.empty else pd.DataFrame()
            if timeline_df.empty:
                empty_state("No Timeline Rows", "No filtered rules are available.")
            else:
                timeline_df["time"] = timeline_df["order"].map(lambda value: f"T+{int(value):02d}")
                timeline_df = timeline_df[["time", "rule_id", "status"]]
                compact_data_table(
                    timeline_df.astype(str).to_dict("records"),
                    columns=["time", "rule_id", "status"],
                    max_rows=len(timeline_df),
                )

    with lower_mid:
        with panel("Severity Breakdown", "Passed, review, and blocked audit states", height=360, scroll=True):
            severity_rows = [
                {"status": "passed", "count": passed},
                {"status": "review", "count": warnings},
                {"status": "blocked", "count": blocked},
            ]
            compact_data_table(
                severity_rows,
                columns=["status", "count"],
                max_rows=len(severity_rows),
            )
            vspace(10)
            st.markdown(
                f"""
                <div class="fs-rule-health-strip">
                  <div><span>{passed:,}</span><small>passed</small></div>
                  <div><span>{warnings:,}</span><small>review</small></div>
                  <div><span>{blocked:,}</span><small>blocked</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with lower_right:
        with panel("Representative Rule Validation", "Readable execution rows for core rule domains", height=360, scroll=True):
            representative = [
                record
                for record in records
                if str(record.get("prefix")) in {"DATA", "SCHEMA", "METRIC", "VIS", "INSIGHT", "SAFE"}
            ]
            rule_validation_list(representative or records, limit=8)

    st.markdown('<div class="fs-row-spacer fs-row-spacer-sm"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Layout override: Applied Rules tab v11.1
# Appended by apply_applied_rules_layout_v11_1.py.
# This later definition intentionally overrides v11 render_applied_rules_tab.
# ---------------------------------------------------------------------------
def render_applied_rules_tab(
    df: pd.DataFrame | None,
    audit: RuleAuditLog,
) -> None:
    """Render the Applied Rules tab as a full audit browser.

    v11.1 moves the search input into the Rules Table card. In v11 the search
    input was rendered above the KPI row, which made it feel detached from the
    table it controls.
    """

    if not _analysis_available(df):
        return

    records = _rule_records(audit)
    summary = _rule_summary(records)

    if not records:
        empty_state("No Applied Rules", "Rule audit records will appear after analysis.")
        return

    rules_df = pd.DataFrame(records).copy()
    preferred_cols = ["rule_id", "prefix", "step", "severity", "result"]
    available_cols = [col for col in preferred_cols if col in rules_df.columns]
    rules_df = rules_df[available_cols].copy()

    rules_df.insert(0, "order", range(1, len(rules_df) + 1))
    rules_df["status"] = rules_df["severity"].map(
        lambda value: "review" if str(value).upper() == "WARNING" else "blocked" if str(value).upper() == "ERROR" else "passed"
    )

    search_key = "applied_rules_search_v11_1"
    search = str(st.session_state.get(search_key, "")).strip()

    filtered_df = rules_df
    if search:
        mask = rules_df.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered_df = rules_df[mask].copy()

    warnings = int((rules_df["severity"].astype(str).str.upper() == "WARNING").sum()) if "severity" in rules_df.columns else 0
    blocked = int((rules_df["severity"].astype(str).str.upper() == "ERROR").sum()) if "severity" in rules_df.columns else 0
    passed = max(len(rules_df) - warnings - blocked, 0)

    top_cols = st.columns(5)
    with top_cols[0]:
        metric_card("Rules Executed", f"{len(records):,}", "Deduplicated audit records", "teal", "#")
    with top_cols[1]:
        metric_card("Visible Rows", f"{len(filtered_df):,}", "After search filter", "blue", "F")
    with top_cols[2]:
        metric_card("Coverage", f"{summary['coverage']}/{summary['required']}", "Required Skill categories", "purple", "C")
    with top_cols[3]:
        metric_card("Warnings", f"{warnings:,}", "Review-level records", "amber" if warnings else "teal", "!")
    with top_cols[4]:
        metric_card("Blocked", f"{blocked:,}", "Error-level records", "red" if blocked else "teal", "X")

    vspace(16)

    left, right = st.columns([1.72, 1.0])
    with left:
        with panel(
            "Rules Table",
            f"Showing {len(filtered_df):,} of {len(rules_df):,} executed rule records",
            height=560,
            scroll=True,
        ):
            st.text_input(
                "Search rules",
                placeholder="Search by rule ID, prefix, step, severity, or result...",
                label_visibility="collapsed",
                key=search_key,
            )
            st.markdown('<div class="fs-rules-table-search-gap"></div>', unsafe_allow_html=True)

            if filtered_df.empty:
                empty_state("No Matching Rules", "No rule audit records matched the current search.")
            else:
                display_cols = ["order", "rule_id", "prefix", "step", "severity", "status", "result"]
                display_cols = [col for col in display_cols if col in filtered_df.columns]
                compact_data_table(
                    filtered_df.astype(str).to_dict("records"),
                    columns=display_cols,
                    max_rows=len(filtered_df),
                )

    with right:
        with panel("Governance Overview", "Coverage, severity, and source status", height=260, scroll=True):
            integrity_grade = "A+" if blocked == 0 and summary["coverage"] == summary["required"] else "A" if blocked == 0 else "Review"
            st.markdown(
                f"""
                <div class="fs-governance-grade">
                  <div class="fs-governance-grade-label">System Integrity</div>
                  <div class="fs-governance-grade-value">{integrity_grade}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            rows = [
                {"item": "Rule Coverage", "value": f"{summary['coverage']}/{summary['required']}"},
                {"item": "Rules Executed", "value": f"{summary['executed']:,}"},
                {"item": "Passed", "value": f"{passed:,}"},
                {"item": "Warnings", "value": f"{warnings:,}"},
                {"item": "Blocked", "value": f"{blocked:,}"},
                {"item": "Loaded From", "value": "Skills.md"},
            ]
            key_value_table(rows)

        vspace(12)

        with panel("Rule Domains", "Executed records grouped by rule prefix", height=288, scroll=True):
            if "prefix" not in rules_df.columns:
                empty_state("No Prefix Data", "Rule prefix metadata is unavailable.")
            else:
                domain_rows = (
                    rules_df.groupby("prefix", dropna=False)
                    .size()
                    .reset_index(name="rules")
                    .sort_values("rules", ascending=False)
                )
                compact_data_table(
                    domain_rows.astype(str).to_dict("records"),
                    columns=["prefix", "rules"],
                    max_rows=len(domain_rows),
                )

    vspace(10)

    lower_left, lower_mid, lower_right = st.columns([1.05, 1.0, 1.25])
    with lower_left:
        with panel("Execution Timeline", "First-to-last audit execution order", height=360, scroll=True):
            timeline_df = filtered_df[["order", "rule_id", "status"]].copy() if not filtered_df.empty else pd.DataFrame()
            if timeline_df.empty:
                empty_state("No Timeline Rows", "No filtered rules are available.")
            else:
                timeline_df["time"] = timeline_df["order"].map(lambda value: f"T+{int(value):02d}")
                timeline_df = timeline_df[["time", "rule_id", "status"]]
                compact_data_table(
                    timeline_df.astype(str).to_dict("records"),
                    columns=["time", "rule_id", "status"],
                    max_rows=len(timeline_df),
                )

    with lower_mid:
        with panel("Severity Breakdown", "Passed, review, and blocked audit states", height=360, scroll=True):
            severity_rows = [
                {"status": "passed", "count": passed},
                {"status": "review", "count": warnings},
                {"status": "blocked", "count": blocked},
            ]
            compact_data_table(
                severity_rows,
                columns=["status", "count"],
                max_rows=len(severity_rows),
            )
            vspace(10)
            st.markdown(
                f"""
                <div class="fs-rule-health-strip">
                  <div><span>{passed:,}</span><small>passed</small></div>
                  <div><span>{warnings:,}</span><small>review</small></div>
                  <div><span>{blocked:,}</span><small>blocked</small></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with lower_right:
        with panel("Representative Rule Validation", "Readable execution rows for core rule domains", height=360, scroll=True):
            representative = [
                record
                for record in records
                if str(record.get("prefix")) in {"DATA", "SCHEMA", "METRIC", "VIS", "INSIGHT", "SAFE"}
            ]
            rule_validation_list(representative or records, limit=8)

    st.markdown('<div class="fs-row-spacer fs-row-spacer-sm"></div>', unsafe_allow_html=True)
