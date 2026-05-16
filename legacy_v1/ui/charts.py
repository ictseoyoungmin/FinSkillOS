"""Chart renderers used by FinSkillOS UI tabs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.components import empty_state
from ui.theme import style_plotly_figure


PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def _render_plotly(fig: go.Figure) -> None:
    st.plotly_chart(style_plotly_figure(fig), use_container_width=True, config=PLOTLY_CONFIG)


def render_cumulative_return_chart(metrics: dict[str, Any] | None, height: int = 320) -> None:
    if not metrics:
        empty_state("Cumulative Return Unavailable", "Run an analysis to generate return series.")
        return
    cumulative = metrics.get("cumulative_returns")
    if not isinstance(cumulative, pd.DataFrame) or cumulative.empty:
        empty_state("Cumulative Return Unavailable", "No cumulative return series was produced for this schema.")
        return

    plot_df = cumulative.copy()
    plot_df["indexed_value"] = 100.0 * (1.0 + plot_df["cumulative_return"])
    fig = px.line(plot_df, x="date", y="indexed_value", color="asset")
    fig.update_layout(height=height)
    fig.update_yaxes(title="Indexed Value")
    _render_plotly(fig)


def render_drawdown_chart(metrics: dict[str, Any] | None, height: int = 320) -> None:
    if not metrics:
        empty_state("Drawdown Unavailable", "Run an analysis to generate drawdown series.")
        return
    drawdowns = metrics.get("drawdowns")
    if not isinstance(drawdowns, pd.DataFrame) or drawdowns.empty:
        empty_state("Drawdown Unavailable", "Drawdown requires a valid price or return time series.")
        return

    fig = px.area(drawdowns, x="date", y="drawdown", color="asset")
    fig.update_layout(height=height)
    fig.update_yaxes(tickformat=".0%", title="Drawdown")
    _render_plotly(fig)


def render_correlation_heatmap(metrics: dict[str, Any] | None, height: int = 280) -> None:
    if not metrics:
        empty_state("Correlation Unavailable", "Run an analysis to generate asset return correlations.")
        return
    corr = metrics.get("correlation_matrix")
    if not isinstance(corr, pd.DataFrame) or corr.empty:
        empty_state("Correlation Unavailable", "Correlation heatmap requires at least two assets with overlapping returns.")
        return

    fig = px.imshow(
        corr,
        text_auto=".2f",
        zmin=-1,
        zmax=1,
        color_continuous_scale="RdBu_r",
        aspect="auto",
    )
    fig.update_layout(height=height)
    _render_plotly(fig)


def render_risk_return_scatter(metrics: dict[str, Any] | None, height: int = 280) -> None:
    if not metrics:
        empty_state("Risk vs. Return Unavailable", "Run an analysis to generate asset-level metrics.")
        return

    asset_metrics = pd.DataFrame(metrics.get("asset_metrics", []))
    required = {"annualized_volatility", "annualized_return", "asset"}
    if asset_metrics.empty or not required.issubset(asset_metrics.columns):
        empty_state("Risk vs. Return Unavailable", "This panel requires asset, annualized return, and volatility metrics.")
        return

    asset_metrics = asset_metrics.dropna(subset=["annualized_volatility", "annualized_return"])
    if asset_metrics.empty:
        empty_state("Risk vs. Return Unavailable", "No asset has both return and volatility available.")
        return

    size = asset_metrics["max_drawdown"].abs() if "max_drawdown" in asset_metrics.columns else None
    fig = px.scatter(
        asset_metrics,
        x="annualized_volatility",
        y="annualized_return",
        text="asset",
        size=size,
    )
    fig.update_layout(height=height)
    fig.update_traces(textposition="top center")
    fig.update_xaxes(tickformat=".0%", title="Volatility")
    fig.update_yaxes(tickformat=".0%", title="Annualized Return")
    _render_plotly(fig)


def render_missing_values_chart(profile: dict[str, Any] | None, height: int = 250) -> None:
    if not profile:
        empty_state("Missingness Unavailable", "Run an analysis to inspect missing values.")
        return
    missing = profile.get("missing_rates", {})
    if not missing:
        empty_state("Missingness Unavailable", "No column missingness profile was produced.")
        return
    plot_df = pd.DataFrame(
        [{"column": column, "missing_rate": float(rate), "completeness": 1.0 - float(rate)} for column, rate in missing.items()]
    ).sort_values("missing_rate", ascending=False)
    if plot_df["missing_rate"].max() <= 0:
        fig = px.bar(
            plot_df,
            x="column",
            y="completeness",
            text=plot_df["completeness"].map(lambda value: f"{value:.1%}"),
            color_discrete_sequence=["#00d4a0"],
        )
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_yaxes(tickformat=".0%", title="Completeness", range=[0, 1.08])
    else:
        fig = px.bar(
            plot_df,
            x="column",
            y="missing_rate",
            text=plot_df["missing_rate"].map(lambda value: f"{value:.1%}"),
            color_discrete_sequence=["#f05151"],
        )
        max_rate = max(float(plot_df["missing_rate"].max()), 0.01)
        fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig.update_yaxes(tickformat=".1%", title="Missing Rate", range=[0, min(max_rate * 1.35, 1.0)])
    fig.update_layout(height=height, showlegend=False)
    fig.update_xaxes(title="")
    _render_plotly(fig)


def render_frequency_coverage_chart(schema: dict[str, Any] | None, height: int = 250) -> None:
    """Render a readable coverage chart.

    The previous implementation rendered one bar per date. For daily market
    data this can produce hundreds of dense bars that look like vertical stripes.
    This version automatically aggregates the coverage view:

    - <= 45 unique dates: daily active rows
    - <= 180 unique dates: weekly active dates
    - > 180 unique dates: monthly active dates

    The bar shows active dates in each period. The line shows average rows per
    active date, which is usually the number of assets observed on each date.
    """

    std_df = schema.get("standardized_df") if schema else None
    if not isinstance(std_df, pd.DataFrame) or "date" not in std_df.columns:
        empty_state("Coverage Unavailable", "Coverage requires a standardized date column.")
        return

    working = std_df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date"])
    if working.empty:
        empty_state("Coverage Unavailable", "No valid dates were available after standardization.")
        return

    daily = (
        working.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "rows"})
        .sort_values("date")
    )
    if daily.empty:
        empty_state("Coverage Unavailable", "No valid dates were available after standardization.")
        return

    unique_dates = int(daily["date"].nunique())
    date_span_days = max(int((daily["date"].max() - daily["date"].min()).days) + 1, 1)

    if unique_dates <= 45:
        plot_df = daily.rename(columns={"date": "period", "rows": "avg_rows_per_active_date"})
        plot_df["active_dates"] = 1
        period_label = "Daily"
        bar_title = "Active Date"
        x_title = ""
    else:
        rule = "W-MON" if unique_dates <= 180 else "ME"
        period_label = "Weekly" if unique_dates <= 180 else "Monthly"
        x_title = "Week" if unique_dates <= 180 else "Month"

        plot_df = (
            daily.set_index("date")
            .resample(rule)
            .agg(
                active_dates=("rows", "count"),
                total_rows=("rows", "sum"),
                avg_rows_per_active_date=("rows", "mean"),
            )
            .reset_index()
            .rename(columns={"date": "period"})
        )
        plot_df = plot_df[plot_df["active_dates"] > 0]
        bar_title = "Active Dates"

    if plot_df.empty:
        empty_state("Coverage Unavailable", "Coverage aggregation produced no displayable periods.")
        return

    max_active_dates = max(float(plot_df["active_dates"].max()), 1.0)
    avg_rows_max = max(float(plot_df["avg_rows_per_active_date"].max()), 1.0)
    coverage_ratio = unique_dates / date_span_days

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=plot_df["period"],
            y=plot_df["active_dates"],
            name=bar_title,
            marker=dict(
                color="rgba(37, 242, 199, 0.72)",
                line=dict(color="rgba(37, 242, 199, 0.92)", width=0.8),
            ),
            hovertemplate=(
                f"{period_label} period: %{{x|%Y-%m-%d}}<br>"
                "Active dates: %{y}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=plot_df["period"],
            y=plot_df["avg_rows_per_active_date"],
            name="Avg rows / active date",
            mode="lines+markers",
            yaxis="y2",
            line=dict(width=2.2, color="#38a3ff"),
            marker=dict(size=5, color="#38a3ff"),
            hovertemplate=(
                f"{period_label} period: %{{x|%Y-%m-%d}}<br>"
                "Avg rows / active date: %{y:.2f}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_annotation(
        x=0.01,
        y=1.08,
        xref="paper",
        yref="paper",
        text=f"{period_label} view · {unique_dates:,} active dates · {coverage_ratio:.1%} calendar coverage",
        showarrow=False,
        align="left",
        font=dict(size=11, color="#7a8ba0"),
    )

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=42, b=14),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            xanchor="right",
            x=1.0,
            font=dict(size=10),
        ),
        bargap=0.18 if len(plot_df) <= 24 else 0.08,
        yaxis=dict(
            title=bar_title,
            range=[0, max_active_dates * 1.22],
            gridcolor="rgba(129, 166, 202, 0.14)",
            zerolinecolor="rgba(129, 166, 202, 0.20)",
        ),
        yaxis2=dict(
            title="Avg Rows",
            overlaying="y",
            side="right",
            range=[0, avg_rows_max * 1.35],
            showgrid=False,
            zeroline=False,
        ),
    )

    fig.update_xaxes(title=x_title, tickfont=dict(size=10))
    _render_plotly(fig)

def render_return_distribution(metrics: dict[str, Any] | None, height: int = 270) -> None:
    if not metrics:
        empty_state("Return Distribution Unavailable", "Run an analysis to generate return observations.")
        return
    returns = metrics.get("returns")
    if not isinstance(returns, pd.DataFrame) or returns.empty or "return" not in returns.columns:
        empty_state("Return Distribution Unavailable", "Return distribution requires period return observations.")
        return
    fig = px.histogram(returns.dropna(subset=["return"]), x="return", nbins=36, color="asset" if "asset" in returns.columns else None)
    fig.update_layout(height=height, bargap=0.04)
    fig.update_xaxes(tickformat=".1%", title="Period Return")
    fig.update_yaxes(title="Frequency")
    _render_plotly(fig)


def _portfolio_return_series(metrics: dict[str, Any]) -> pd.DataFrame:
    returns = metrics.get("returns")
    if not isinstance(returns, pd.DataFrame) or returns.empty or not {"date", "return"}.issubset(returns.columns):
        return pd.DataFrame()
    working = returns.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working["return"] = pd.to_numeric(working["return"], errors="coerce")
    working = working.dropna(subset=["date", "return"])
    if working.empty:
        return pd.DataFrame()
    return working.groupby("date", as_index=False)["return"].mean().sort_values("date")


def render_monthly_returns_heatmap(metrics: dict[str, Any] | None, height: int = 300) -> None:
    if not metrics:
        empty_state("Monthly Returns Unavailable", "Run an analysis to generate monthly return observations.")
        return
    portfolio = _portfolio_return_series(metrics)
    if portfolio.empty:
        empty_state("Monthly Returns Unavailable", "Monthly heatmap requires dated return observations.")
        return

    monthly = (
        portfolio.set_index("date")["return"]
        .resample("ME")
        .apply(lambda series: (1.0 + series).prod() - 1.0)
        .dropna()
        .reset_index()
    )
    if monthly.empty:
        empty_state("Monthly Returns Unavailable", "Not enough dated returns were available for monthly aggregation.")
        return

    monthly["year"] = monthly["date"].dt.year.astype(str)
    monthly["month"] = monthly["date"].dt.strftime("%b")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    heatmap = monthly.pivot_table(index="year", columns="month", values="return", aggfunc="last").reindex(columns=month_order)
    heatmap = heatmap.sort_index(ascending=False)
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap.to_numpy(),
            x=list(heatmap.columns),
            y=list(heatmap.index),
            colorscale=[
                [0.0, "#4a1022"],
                [0.45, "#151e2d"],
                [0.55, "#123027"],
                [1.0, "#00d4a0"],
            ],
            zmid=0,
            xgap=2,
            ygap=2,
            colorbar=dict(title="Return", tickformat=".0%", thickness=10, len=0.76),
            hovertemplate="%{y} %{x}<br>Return %{z:.2%}<extra></extra>",
        )
    )
    fig.update_layout(height=height, margin=dict(l=12, r=8, t=14, b=12), xaxis_title="", yaxis_title="")
    fig.update_xaxes(side="bottom", tickfont=dict(size=9))
    fig.update_yaxes(tickfont=dict(size=9))
    _render_plotly(fig)


def render_var_cvar_distribution(metrics: dict[str, Any] | None, height: int = 285) -> None:
    if not metrics:
        empty_state("VaR Distribution Unavailable", "Run an analysis to generate risk observations.")
        return
    portfolio = _portfolio_return_series(metrics)
    if portfolio.empty:
        empty_state("VaR Distribution Unavailable", "VaR distribution requires dated return observations.")
        return

    returns = portfolio["return"].dropna()
    if returns.empty:
        empty_state("VaR Distribution Unavailable", "No valid returns were available for risk distribution.")
        return
    summary = metrics.get("summary", {})
    var_95 = summary.get("historical_var_95")
    var_99 = summary.get("historical_var_99")
    cvar_95 = returns[returns <= var_95].mean() if var_95 is not None and (returns <= var_95).any() else None

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=returns,
            nbinsx=36,
            marker=dict(color="#00d4a0", line=dict(width=0)),
            opacity=0.82,
            name="Portfolio Returns",
            hovertemplate="Return %{x:.2%}<br>Count %{y}<extra></extra>",
        )
    )
    markers = [
        ("VaR 95%", var_95, "#a78bfa"),
        ("VaR 99%", var_99, "#f05151"),
        ("CVaR 95%", cvar_95, "#f5a623"),
    ]
    for label, value, color in markers:
        if value is None or pd.isna(value):
            continue
        fig.add_vline(
            x=float(value),
            line_width=1.6,
            line_dash="dash",
            line_color=color,
        )
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=color, width=1.6, dash="dash"),
                name=f"{label} {float(value):.2%}",
                hoverinfo="skip",
            )
        )
    fig.update_layout(height=height, bargap=0.04, showlegend=True)
    fig.update_xaxes(tickformat=".1%", title="Period Return")
    fig.update_yaxes(title="Frequency")
    _render_plotly(fig)


def render_rolling_return_chart(metrics: dict[str, Any] | None, window: int = 63, height: int = 270) -> None:
    if not metrics:
        empty_state("Rolling Return Unavailable", "Run an analysis to generate returns.")
        return
    returns = metrics.get("returns")
    if not isinstance(returns, pd.DataFrame) or returns.empty or not {"date", "return"}.issubset(returns.columns):
        empty_state("Rolling Return Unavailable", "Rolling return requires dated return observations.")
        return
    working = returns.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date", "return"]).sort_values(["asset", "date"] if "asset" in working.columns else ["date"])
    if "asset" not in working.columns:
        working["asset"] = "Portfolio"
    working["return"] = pd.to_numeric(working["return"], errors="coerce")
    working = working.dropna(subset=["return"])
    try:
        requested_window = max(1, int(window))
    except (TypeError, ValueError):
        requested_window = 63
    min_periods = 5

    def _rolling_compound(series: pd.Series) -> pd.Series:
        effective_window = min(requested_window, len(series))
        if effective_window < min_periods:
            return pd.Series(np.nan, index=series.index)
        return (1.0 + series).rolling(window=effective_window, min_periods=min_periods).apply(
            lambda values: values.prod() - 1.0,
            raw=True,
        )

    working["rolling_return"] = working.groupby("asset")["return"].transform(_rolling_compound)
    plot_df = working.dropna(subset=["rolling_return"])
    if plot_df.empty:
        empty_state("Rolling Return Unavailable", "Not enough observations for the selected rolling window.")
        return
    fig = px.line(plot_df, x="date", y="rolling_return", color="asset")
    fig.update_layout(height=height)
    fig.update_yaxes(tickformat=".0%", title=f"Rolling {window} Period Return")
    _render_plotly(fig)


def render_rolling_volatility_chart(metrics: dict[str, Any] | None, periods_per_year: int = 252, window: int = 63, height: int = 300) -> None:
    if not metrics:
        empty_state("Rolling Volatility Unavailable", "Run an analysis to generate returns.")
        return
    returns = metrics.get("returns")
    if not isinstance(returns, pd.DataFrame) or returns.empty or not {"date", "return"}.issubset(returns.columns):
        empty_state("Rolling Volatility Unavailable", "Rolling volatility requires dated return observations.")
        return
    working = returns.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date", "return"]).sort_values(["asset", "date"] if "asset" in working.columns else ["date"])
    if "asset" not in working.columns:
        working["asset"] = "Portfolio"
    working["return"] = pd.to_numeric(working["return"], errors="coerce")
    working = working.dropna(subset=["return"])
    try:
        requested_window = max(1, int(window))
    except (TypeError, ValueError):
        requested_window = 63
    effective_window = min(requested_window, max(len(working), 1))
    if effective_window < 5:
        empty_state("Rolling Volatility Unavailable", "Not enough observations for the selected rolling window.")
        return
    working["rolling_volatility"] = working.groupby("asset")["return"].transform(
        lambda series: series.rolling(window=effective_window, min_periods=5).std() * (periods_per_year ** 0.5)
    )
    plot_df = working.dropna(subset=["rolling_volatility"])
    if plot_df.empty:
        empty_state("Rolling Volatility Unavailable", "Not enough observations for the selected rolling window.")
        return
    fig = px.line(plot_df, x="date", y="rolling_volatility", color="asset")
    fig.update_layout(height=height)
    fig.update_yaxes(tickformat=".0%", title="Annualized Volatility")
    _render_plotly(fig)


def render_allocation_chart(schema: dict[str, Any] | None, height: int = 280) -> None:
    std_df = schema.get("standardized_df") if schema else None
    if not isinstance(std_df, pd.DataFrame) or not {"asset", "weight"}.issubset(std_df.columns):
        empty_state("Allocation Unavailable", "Allocation chart requires standardized asset and weight fields.")
        return
    plot_df = std_df.dropna(subset=["asset", "weight"])
    if plot_df.empty:
        empty_state("Allocation Unavailable", "No valid asset weights were available.")
        return
    fig = px.pie(plot_df, names="asset", values="weight", hole=0.48)
    fig.update_layout(height=height)
    _render_plotly(fig)


def render_risk_contribution_chart(metrics: dict[str, Any] | None, height: int = 280) -> None:
    if not metrics:
        empty_state("Risk Contribution Unavailable", "Run an analysis to generate asset metrics.")
        return
    asset_metrics = pd.DataFrame(metrics.get("asset_metrics", []))
    if asset_metrics.empty or not {"asset", "annualized_volatility"}.issubset(asset_metrics.columns):
        empty_state("Risk Contribution Unavailable", "Risk contribution requires asset-level volatility metrics.")
        return
    plot_df = asset_metrics.dropna(subset=["annualized_volatility"]).copy()
    total = plot_df["annualized_volatility"].sum()
    if total == 0 or plot_df.empty:
        empty_state("Risk Contribution Unavailable", "Asset volatility values are unavailable or zero.")
        return
    plot_df["risk_contribution"] = plot_df["annualized_volatility"] / total
    fig = px.bar(plot_df.sort_values("risk_contribution"), x="risk_contribution", y="asset", orientation="h")
    fig.update_layout(height=height)
    fig.update_xaxes(tickformat=".0%", title="Share of Asset Volatility")
    fig.update_yaxes(title="")
    _render_plotly(fig)
