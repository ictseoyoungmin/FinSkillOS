"""Risk-first insight generation and financial safety checks."""

from __future__ import annotations

from typing import Any
import re

import numpy as np
import pandas as pd

from engine.metrics import format_percent, format_ratio
from engine.rule_engine import AppliedRule, RuleAuditLog


FORBIDDEN_TERMS = (
    "매수",
    "매도",
    "보유",
    "추천",
    "투자하세요",
    "투자하기",
    "진입",
    "손절",
    "익절",
    "확실",
    "보장",
    "매수하세요",
    "매도하세요",
    "보유하세요",
    "추천합니다",
    "투자하세요",
    "진입하세요",
    "손절하세요",
    "익절하세요",
    "확실합니다",
    "보장됩니다",
    "buy",
    "sell",
    "hold",
    "strong buy",
    "strong sell",
    "guaranteed",
    "risk-free profit",
    "must invest",
)

PRIORITY = {
    "data_quality": 1,
    "high_risk": 2,
    "drawdown": 3,
    "volatility": 4,
    "concentration": 5,
    "return": 6,
    "sharpe": 7,
    "correlation": 8,
}


def _severity_from_level(level: str | None) -> str:
    if level in {"VERY HIGH", "HIGH"}:
        return "HIGH"
    if level == "MODERATE":
        return "MEDIUM"
    return "INFO"


def _contains_forbidden(text: str) -> list[str]:
    lowered = text.lower()
    blocked = []
    for term in FORBIDDEN_TERMS:
        escaped = re.escape(term.lower())
        if term.isascii() and term.replace(" ", "").isalpha():
            pattern = rf"\b{escaped}\b"
        else:
            pattern = escaped
        if re.search(pattern, lowered):
            blocked.append(term)
    return blocked


def _rewrite_if_needed(text: str) -> tuple[str, list[str]]:
    blocked = _contains_forbidden(text)
    if not blocked:
        return text, []
    return (
        "The observed data shows an analysis signal that needs additional risk review, without recommending a specific investment action.",
        blocked,
    )


def _safe_insight(insight: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    blocked_terms: list[str] = []
    if not insight.get("evidence"):
        return None, blocked_terms
    for key in ("fact", "interpretation", "caution"):
        rewritten, blocked = _rewrite_if_needed(str(insight.get(key, "")))
        insight[key] = rewritten
        blocked_terms.extend(blocked)
    if not insight.get("caution"):
        insight["caution"] = "Review data limitations and possible market regime changes before using this result."
    return insight, blocked_terms


def _insight(
    category: str,
    severity: str,
    fact: str,
    interpretation: str,
    caution: str,
    evidence: dict[str, Any],
    rule_ids: list[str],
) -> dict[str, Any]:
    return {
        "category": category,
        "severity": severity,
        "fact": fact,
        "interpretation": interpretation,
        "caution": caution,
        "evidence": evidence,
        "rule_ids": rule_ids,
    }


def _quality_insight(quality: dict[str, Any]) -> dict[str, Any] | None:
    warnings = quality.get("quality_warnings", []) if quality else []
    if not warnings:
        return None
    return _insight(
        category="data_quality",
        severity="WARNING",
        fact=f"{len(warnings)} data quality warning(s) were detected.",
        interpretation="Some analytics may be affected by missing values, date structure, short observation windows, or outlier candidates.",
        caution="Validate the source data and warning details before using the analysis.",
        evidence={"warning_count": len(warnings), "rule_id": "INSIGHT-CAT-007"},
        rule_ids=["INSIGHT-CAT-007", "INSIGHT-004"],
    )


def _drawdown_insight(summary: dict[str, Any]) -> dict[str, Any] | None:
    max_drawdown = summary.get("max_drawdown")
    if max_drawdown is None:
        return None
    level = summary.get("drawdown_risk_level", "UNKNOWN")
    return _insight(
        category="drawdown",
        severity=_severity_from_level(level),
        fact=f"Maximum drawdown is {format_percent(max_drawdown)}.",
        interpretation=f"Under RISK-001, drawdown risk is classified as {level}.",
        caution="Maximum drawdown is a historical observation, not a future loss limit.",
        evidence={"metric": "max_drawdown", "value": max_drawdown, "rule_id": "RISK-001", "chart": "drawdown"},
        rule_ids=["INSIGHT-CAT-003", "RISK-001"],
    )


def _volatility_insight(summary: dict[str, Any]) -> dict[str, Any] | None:
    volatility = summary.get("annualized_volatility")
    if volatility is None:
        return None
    level = summary.get("volatility_risk_level", "UNKNOWN")
    return _insight(
        category="volatility",
        severity=_severity_from_level(level),
        fact=f"Annualized volatility is {format_percent(volatility)}.",
        interpretation=f"Under RISK-002, volatility risk is classified as {level}.",
        caution="Volatility measures the size of price moves and does not only represent downside loss.",
        evidence={"metric": "annualized_volatility", "value": volatility, "rule_id": "RISK-002"},
        rule_ids=["INSIGHT-CAT-002", "RISK-002"],
    )


def _concentration_insight(metrics: dict[str, Any]) -> dict[str, Any] | None:
    allocation = metrics.get("allocation", {})
    if not allocation:
        return None
    max_weight = allocation.get("max_weight")
    hhi = allocation.get("hhi")
    level = allocation.get("concentration_level", "UNKNOWN")
    return _insight(
        category="concentration",
        severity="HIGH" if level == "HIGH" else "MEDIUM" if level == "MODERATE" else "INFO",
        fact=f"The largest asset weight is {format_percent(max_weight)} and HHI is {format_ratio(hhi)}.",
        interpretation=f"Under METRIC-015, concentration is classified as {level}.",
        caution="Concentration can increase return contribution, but it can also amplify loss concentration risk.",
        evidence={"metric": "max_weight/hhi", "value": {"max_weight": max_weight, "hhi": hhi}, "rule_id": "METRIC-015"},
        rule_ids=["INSIGHT-CAT-006", "METRIC-015"],
    )


def _return_insight(summary: dict[str, Any]) -> dict[str, Any] | None:
    total_return = summary.get("total_return")
    if total_return is None:
        return None
    direction = "positive" if total_return >= 0 else "negative"
    return _insight(
        category="return",
        severity="INFO",
        fact=f"Cumulative return over the observation window is {format_percent(total_return)}.",
        interpretation=f"Performance direction over the same window is {direction}.",
        caution="Return is sensitive to the selected observation window and may change with a different period.",
        evidence={"metric": "total_return", "value": total_return, "rule_id": "METRIC-003"},
        rule_ids=["INSIGHT-CAT-001", "METRIC-003"],
    )


def _sharpe_insight(summary: dict[str, Any]) -> dict[str, Any] | None:
    sharpe = summary.get("sharpe_ratio")
    if sharpe is None:
        return None
    quality = summary.get("sharpe_quality", "N/A")
    return _insight(
        category="sharpe",
        severity="INFO" if sharpe >= 0 else "WARNING",
        fact=f"Sharpe Ratio is {format_ratio(sharpe)}.",
        interpretation=f"Under RISK-003, risk-adjusted performance is classified as {quality}.",
        caution="Sharpe Ratio depends on assumptions about the stability of the return distribution.",
        evidence={"metric": "sharpe_ratio", "value": sharpe, "rule_id": "RISK-003"},
        rule_ids=["INSIGHT-CAT-004", "RISK-003"],
    )


def _correlation_insight(metrics: dict[str, Any]) -> dict[str, Any] | None:
    corr = metrics.get("correlation_matrix")
    if not isinstance(corr, pd.DataFrame) or corr.empty or corr.shape[0] < 2:
        return None
    values = corr.to_numpy(dtype=float)
    mask = ~np.eye(values.shape[0], dtype=bool)
    avg_corr = float(np.nanmean(values[mask]))
    return _insight(
        category="correlation",
        severity="MEDIUM" if avg_corr > 0.7 else "INFO",
        fact=f"Average cross-asset correlation is {avg_corr:.2f}.",
        interpretation="Higher correlation can limit diversification benefits.",
        caution="Correlation can change across market regimes.",
        evidence={"metric": "average_correlation", "value": avg_corr, "rule_id": "METRIC-013", "chart": "correlation_heatmap"},
        rule_ids=["INSIGHT-CAT-005", "METRIC-013"],
    )


def _rank(insight: dict[str, Any]) -> tuple[int, int]:
    severity_rank = {"HIGH": 0, "WARNING": 1, "MEDIUM": 2, "INFO": 3}
    category = insight.get("category", "")
    if insight.get("severity") == "HIGH" and category in {"drawdown", "volatility"}:
        category = "high_risk"
    return (PRIORITY.get(category, 99), severity_rank.get(insight.get("severity"), 9))


def generate_insights(metrics: dict[str, Any], quality: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Generate risk-first, evidence-linked insights."""

    audit = RuleAuditLog()
    raw: list[dict[str, Any] | None] = []
    summary = metrics.get("summary", {}) if metrics else {}
    raw.extend(
        [
            _quality_insight(quality),
            _drawdown_insight(summary),
            _volatility_insight(summary),
            _concentration_insight(metrics),
            _return_insight(summary),
            _sharpe_insight(summary),
            _correlation_insight(metrics),
        ]
    )

    blocked_terms: list[str] = []
    checked: list[dict[str, Any]] = []
    for item in raw:
        if item is None:
            continue
        safe, blocked = _safe_insight(item)
        blocked_terms.extend(blocked)
        if safe is not None:
            checked.append(safe)

    checked = sorted(checked, key=_rank)[:5]
    for idx, insight in enumerate(checked, start=1):
        insight["id"] = f"insight_{idx:03d}"

    audit.add(
        rule_id="INSIGHT-001",
        step="insight_generation",
        condition="Major insights must use Fact / Interpretation / Caution.",
        action="Generate structured insight cards.",
        result=f"{len(checked)} insight(s) generated.",
    )
    audit.add(
        rule_id="INSIGHT-002",
        step="insight_generation",
        condition="Each insight must include evidence.",
        action="Drop insights without evidence.",
        result="Evidence check applied.",
    )
    audit.add(
        rule_id="INSIGHT-003",
        step="insight_generation",
        condition="Risk and limitation insights should be ordered before return interpretation.",
        action="Rank insights by data quality, high risk, drawdown, volatility, concentration, return, Sharpe, correlation.",
        result="Risk-first ordering applied.",
    )
    audit.add(
        rule_id="SAFE-POST-001",
        step="safety_check",
        condition="Generated insights must not include prohibited financial advice terms.",
        action="Scan and rewrite prohibited wording.",
        result=f"{len(blocked_terms)} prohibited term occurrence(s) handled.",
        severity="WARNING" if blocked_terms else "INFO",
    )
    audit.add(
        rule_id="SAFE-POST-002",
        step="safety_check",
        condition="Insights without evidence must not be shown.",
        action="Filter insights with missing evidence.",
        result="All displayed insights include evidence.",
    )
    audit.add(
        rule_id="SAFE-POST-003",
        step="safety_check",
        condition="Insights should include caution text when uncertainty exists.",
        action="Ensure caution text exists.",
        result="Caution text verified.",
    )

    return {
        "insights": checked,
        "blocked_terms": sorted(set(blocked_terms)),
        "applied_rules": audit.to_records(),
        "schema_type": schema.get("schema_type") if schema else "unknown",
    }
