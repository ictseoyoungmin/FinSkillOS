"""Chart selection planner for FinSkillOS."""

from __future__ import annotations

from typing import Any


def _has_time_series(schema: dict[str, Any]) -> bool:
    std_df = schema.get("standardized_df")
    return hasattr(std_df, "columns") and "date" in std_df.columns


def _has_price(schema: dict[str, Any]) -> bool:
    std_df = schema.get("standardized_df")
    return hasattr(std_df, "columns") and "price" in std_df.columns


def _has_weight(schema: dict[str, Any]) -> bool:
    std_df = schema.get("standardized_df")
    return hasattr(std_df, "columns") and "weight" in std_df.columns


def _asset_metric_count(metrics: dict[str, Any]) -> int:
    return len(metrics.get("asset_metrics", []) or [])


def _add_chart(
    charts: list[dict[str, Any]],
    chart_id: str,
    rule_id: str,
    title: str,
    priority: int,
    reason: str,
    section: str,
    available: bool = True,
) -> None:
    charts.append(
        {
            "chart_id": chart_id,
            "rule_id": rule_id,
            "title": title,
            "priority": priority,
            "reason": reason,
            "section": section,
            "available": available,
        }
    )


def plan_charts(schema: dict[str, Any], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Select charts according to VIS rules."""

    schema_type = schema.get("schema_type", "unknown")
    charts: list[dict[str, Any]] = []
    cumulative = metrics.get("cumulative_returns")
    drawdowns = metrics.get("drawdowns")
    corr = metrics.get("correlation_matrix")
    asset_metrics = metrics.get("asset_metrics", [])

    if schema_type in {"single_asset_price", "single_asset_return"}:
        _add_chart(
            charts,
            "price_trend",
            "VIS-001",
            "Price Trend",
            1,
            "Single asset price data is available.",
            "return_analysis",
            available=_has_time_series(schema) and _has_price(schema),
        )
        _add_chart(
            charts,
            "cumulative_return",
            "VIS-002",
            "Cumulative Return",
            2,
            "Return series can be converted to cumulative return.",
            "return_analysis",
            available=hasattr(cumulative, "empty") and not cumulative.empty,
        )
        _add_chart(
            charts,
            "drawdown",
            "VIS-003",
            "Drawdown",
            3,
            "Return series exists or can be computed from price.",
            "risk_analysis",
            available=hasattr(drawdowns, "empty") and not drawdowns.empty,
        )
        _add_chart(
            charts,
            "metric_summary_table",
            "VIS-006",
            "Metric Summary",
            5,
            "One or more metrics are calculable.",
            "return_analysis",
            available=bool(asset_metrics),
        )

    elif schema_type in {"multi_asset_long", "multi_asset_wide"}:
        _add_chart(
            charts,
            "indexed_cumulative_return",
            "VIS-002",
            "Indexed Cumulative Return Comparison",
            1,
            "Multiple asset return series are available.",
            "return_analysis",
            available=hasattr(cumulative, "empty") and not cumulative.empty,
        )
        _add_chart(
            charts,
            "metric_summary_table",
            "VIS-006",
            "Asset Metric Summary",
            2,
            "Asset-level metrics are calculable.",
            "return_analysis",
            available=_asset_metric_count(metrics) >= 1,
        )
        _add_chart(
            charts,
            "risk_return_scatter",
            "VIS-005",
            "Risk-Return Scatter",
            3,
            "Two or more assets have annualized return and volatility.",
            "correlation_diversification",
            available=_asset_metric_count(metrics) >= 2,
        )
        _add_chart(
            charts,
            "correlation_heatmap",
            "VIS-004",
            "Correlation Heatmap",
            4,
            "Two or more asset return series have sufficient overlap.",
            "correlation_diversification",
            available=hasattr(corr, "empty") and not corr.empty,
        )
        _add_chart(
            charts,
            "drawdown_comparison",
            "VIS-003",
            "Drawdown Comparison",
            5,
            "Drawdown series can be computed for multiple assets.",
            "risk_analysis",
            available=hasattr(drawdowns, "empty") and not drawdowns.empty,
        )

    elif schema_type == "allocation":
        _add_chart(
            charts,
            "allocation_chart",
            "VIS-007",
            "Allocation",
            1,
            "Weight column exists.",
            "return_analysis",
            available=_has_weight(schema),
        )
        _add_chart(
            charts,
            "concentration_table",
            "VIS-006",
            "Concentration Summary",
            2,
            "Concentration metrics are calculable from weights.",
            "risk_analysis",
            available=bool(metrics.get("allocation")),
        )
        _add_chart(
            charts,
            "sector_exposure",
            "VIS-007",
            "Sector Exposure",
            3,
            "Sector/category metadata is available with weights.",
            "correlation_diversification",
            available=_has_weight(schema),
        )

    else:
        _add_chart(
            charts,
            "metric_summary_table",
            "VIS-006",
            "Metric Summary",
            1,
            "Schema is unknown, so only calculable summary outputs can be displayed.",
            "return_analysis",
            available=bool(metrics.get("summary")),
        )

    return sorted(charts, key=lambda item: item["priority"])
