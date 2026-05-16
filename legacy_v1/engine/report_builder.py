"""HTML report builder for FinSkillOS."""

from __future__ import annotations

from typing import Any

import pandas as pd
from jinja2 import Template

from engine.metrics import format_percent, format_ratio


DISCLAIMER = (
    "본 리포트는 사용자가 제공한 데이터에 기반한 분석 결과이며, 특정 금융상품이나 "
    "투자 행동에 대한 지시가 아닙니다. 과거 성과는 미래 결과를 약속하지 않습니다."
)


REPORT_TEMPLATE = Template(
    """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>FinSkillOS Analysis Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17202a; margin: 32px; line-height: 1.5; }
    h1, h2, h3 { color: #17202a; }
    h1 { border-bottom: 2px solid #245b8f; padding-bottom: 10px; }
    h2 { margin-top: 32px; border-top: 1px solid #d8e0e7; padding-top: 18px; page-break-after: avoid; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0 24px; font-size: 13px; }
    caption { text-align: left; font-weight: 700; margin-bottom: 6px; color: #245b8f; }
    th, td { border: 1px solid #d8e0e7; padding: 7px 9px; vertical-align: top; }
    th { background: #f2f6f9; }
    .metric-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
    .metric { border: 1px solid #d8e0e7; padding: 10px 12px; background: #fbfcfd; }
    .metric-label { color: #5f6f7d; font-size: 12px; }
    .metric-value { font-size: 20px; font-weight: 700; }
    .insight { border: 1px solid #d8e0e7; padding: 12px; margin: 10px 0; page-break-inside: avoid; }
    .disclaimer { margin-top: 36px; padding: 14px; border: 1px solid #9a6a16; background: #fff9ec; }
    .small { color: #5f6f7d; font-size: 12px; }
  </style>
</head>
<body>
  <h1>FinSkillOS Analysis Report</h1>
  <p class="small">Skill-Governed Investment Analytics Dashboard</p>

  <h2>1. Dataset Summary</h2>
  <table>
    <caption>Dataset summary</caption>
    <tbody>
      <tr><th>Dataset</th><td>{{ source_name }}</td></tr>
      <tr><th>Analysis Mode</th><td>{{ mode }}</td></tr>
      <tr><th>Rows</th><td>{{ profile.row_count if profile else "N/A" }}</td></tr>
      <tr><th>Columns</th><td>{{ profile.column_count if profile else "N/A" }}</td></tr>
      <tr><th>Frequency</th><td>{{ profile.frequency if profile else "N/A" }}</td></tr>
    </tbody>
  </table>

  <h2>2. Schema Mapping</h2>
  <p>Detected schema: <strong>{{ schema.schema_type if schema else "N/A" }}</strong></p>
  {{ mapping_table_html }}

  <h2>3. Metric Summary</h2>
  <div class="metric-grid">
    <div class="metric"><div class="metric-label">Total Return</div><div class="metric-value">{{ summary.total_return }}</div></div>
    <div class="metric"><div class="metric-label">Annualized Return</div><div class="metric-value">{{ summary.annualized_return }}</div></div>
    <div class="metric"><div class="metric-label">Volatility</div><div class="metric-value">{{ summary.annualized_volatility }}</div></div>
    <div class="metric"><div class="metric-label">Maximum Drawdown</div><div class="metric-value">{{ summary.max_drawdown }}</div></div>
    <div class="metric"><div class="metric-label">Sharpe Ratio</div><div class="metric-value">{{ summary.sharpe_ratio }}</div></div>
    <div class="metric"><div class="metric-label">Risk Level</div><div class="metric-value">{{ summary.risk_level }}</div></div>
  </div>
  {{ asset_metrics_html }}
  {{ allocation_html }}

  <h2>4. Main Charts</h2>
  {{ chart_plan_html }}

  <h2>5. Risk Interpretation</h2>
  {% for insight in insights %}
  <div class="insight">
    <h3>{{ insight.id }} · {{ insight.category }} · {{ insight.severity }}</h3>
    <p><strong>Fact:</strong> {{ insight.fact }}</p>
    <p><strong>Interpretation:</strong> {{ insight.interpretation }}</p>
    <p><strong>Caution:</strong> {{ insight.caution }}</p>
    <p class="small"><strong>Evidence:</strong> {{ insight.evidence }}</p>
  </div>
  {% endfor %}

  <h2>6. Skill Rule Audit Log</h2>
  {{ rule_audit_html }}

  <h2>7. Disclaimer</h2>
  <div class="disclaimer">{{ disclaimer }}</div>
</body>
</html>
"""
)


def _table_html(records: Any, caption: str) -> str:
    if records is None:
        return "<p>N/A</p>"
    if isinstance(records, pd.DataFrame):
        if records.empty:
            return "<p>N/A</p>"
        df = records
    else:
        if not records:
            return "<p>N/A</p>"
        df = pd.DataFrame(records)
    html = df.to_html(index=False, escape=True, border=0)
    html = html.replace("<table border=\"0\" class=\"dataframe\">", "<table>", 1)
    return html.replace("<thead>", f"<caption>{caption}</caption><thead>", 1)


def _summary(metrics: dict[str, Any] | None) -> dict[str, str]:
    summary = metrics.get("summary", {}) if metrics else {}
    return {
        "total_return": format_percent(summary.get("total_return")),
        "annualized_return": format_percent(summary.get("annualized_return")),
        "annualized_volatility": format_percent(summary.get("annualized_volatility")),
        "max_drawdown": format_percent(summary.get("max_drawdown")),
        "sharpe_ratio": format_ratio(summary.get("sharpe_ratio")),
        "risk_level": str(summary.get("risk_level", "UNKNOWN")),
    }


def build_html_report(analysis_result: dict[str, Any]) -> str:
    """Build exportable HTML report with metrics, insights, and applied rules."""

    schema = analysis_result.get("schema")
    metrics = analysis_result.get("metrics")
    insights = (analysis_result.get("insights") or {}).get("insights", [])
    audit_records = analysis_result.get("applied_rules", [])
    chart_plan = analysis_result.get("chart_plan", [])

    allocation = metrics.get("allocation", {}) if metrics else {}
    asset_metrics = metrics.get("asset_metrics", []) if metrics else []

    return REPORT_TEMPLATE.render(
        source_name=analysis_result.get("source_name", "N/A"),
        mode=analysis_result.get("mode", "N/A"),
        profile=analysis_result.get("profile"),
        schema=schema,
        summary=_summary(metrics),
        mapping_table_html=_table_html(schema.get("mapping_table", []) if schema else [], "Schema mapping"),
        asset_metrics_html=_table_html(asset_metrics, "Asset metric summary"),
        allocation_html=_table_html([allocation] if allocation else [], "Allocation concentration"),
        chart_plan_html=_table_html(chart_plan, "Selected chart plan"),
        insights=insights,
        rule_audit_html=_table_html(audit_records, "Applied Skill Rules"),
        disclaimer=DISCLAIMER,
    )
