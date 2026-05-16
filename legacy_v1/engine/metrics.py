"""Financial metric calculation engine for FinSkillOS."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engine.rule_engine import AppliedRule, RuleAuditLog


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value) or np.isinf(value):
            return None
    except TypeError:
        return None
    return float(value)


def _risk_drawdown(max_drawdown: float | None) -> str:
    if max_drawdown is None:
        return "UNKNOWN"
    if max_drawdown >= -0.05:
        return "LOW"
    if max_drawdown >= -0.15:
        return "MODERATE"
    if max_drawdown >= -0.25:
        return "HIGH"
    return "VERY HIGH"


def _risk_volatility(volatility: float | None) -> str:
    if volatility is None:
        return "UNKNOWN"
    if volatility < 0.10:
        return "LOW"
    if volatility < 0.20:
        return "MODERATE"
    if volatility <= 0.35:
        return "HIGH"
    return "VERY HIGH"


def _sharpe_quality(sharpe: float | None) -> str:
    if sharpe is None:
        return "N/A"
    if sharpe < 0:
        return "Negative risk-adjusted performance"
    if sharpe < 0.5:
        return "Weak"
    if sharpe < 1.0:
        return "Moderate"
    if sharpe <= 2.0:
        return "Strong"
    return "Very strong, verify data quality"


def _data_sufficiency(observations: int) -> str:
    if observations < 30:
        return "Very limited history"
    if observations < 60:
        return "Limited history"
    if observations < 252:
        return "Medium history"
    return "Sufficient for annualized statistics"


def _periods_per_year(profile: dict[str, Any] | None) -> int:
    if not profile:
        return 252
    value = profile.get("periods_per_year")
    if isinstance(value, int) and value > 0:
        return value
    return 252


def _returns_from_standardized(std_df: pd.DataFrame, audit: RuleAuditLog) -> pd.DataFrame:
    if std_df.empty:
        return pd.DataFrame()

    working = std_df.copy()
    if "date" in working.columns:
        working["date"] = pd.to_datetime(working["date"], errors="coerce")
    if "asset" not in working.columns:
        working["asset"] = "Portfolio"

    if "return" in working.columns:
        working["return"] = pd.to_numeric(working["return"], errors="coerce")
        numeric = working["return"].dropna()
        if not numeric.empty and numeric.abs().max() > 1 and numeric.abs().max() <= 100:
            working["return"] = working["return"] / 100.0
            audit.add(
                rule_id="METRIC-BASE-001",
                step="return_preparation",
                condition="Return values appear to be percent-scale values.",
                action="Convert percent-scale returns to decimal format.",
                result="Return column divided by 100.",
            )
    elif "price" in working.columns:
        working["price"] = pd.to_numeric(working["price"], errors="coerce")
        sort_columns = ["asset"] + (["date"] if "date" in working.columns else [])
        working = working.sort_values(sort_columns)
        working["return"] = working.groupby("asset")["price"].pct_change()
        audit.add(
            rule_id="METRIC-001",
            step="return_preparation",
            condition="Price series is available.",
            action="Calculate period returns from price.",
            result="period_return_t = price_t / price_t-1 - 1.",
        )
    else:
        return pd.DataFrame()

    keep_cols = [column for column in ["date", "asset", "return", "price", "weight"] if column in working.columns]
    return working[keep_cols]


def _series_metrics(
    returns: pd.Series,
    dates: pd.Series | None,
    periods_per_year: int,
    risk_free_rate: float,
) -> tuple[dict[str, Any], pd.DataFrame]:
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    observation_count = int(len(clean))
    if observation_count == 0:
        return {
            "total_return": None,
            "annualized_return": None,
            "annualized_volatility": None,
            "downside_deviation": None,
            "max_drawdown": None,
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "calmar_ratio": None,
            "historical_var_95": None,
            "historical_var_99": None,
            "observation_count": 0,
            "data_sufficiency": _data_sufficiency(0),
            "missing_reasons": ["No valid return observations."],
        }, pd.DataFrame()

    wealth = (1.0 + clean).cumprod()
    cumulative_return = wealth - 1.0
    total_return = float(wealth.iloc[-1] - 1.0)
    annualized_return = None
    if observation_count > 1:
        annualized_return = float((1.0 + total_return) ** (periods_per_year / observation_count) - 1.0)

    volatility = float(clean.std(ddof=1) * np.sqrt(periods_per_year)) if observation_count > 1 else None
    downside = np.minimum(clean, 0.0)
    downside_deviation = float(np.sqrt(np.mean(np.square(downside))) * np.sqrt(periods_per_year))
    running_max = pd.concat(
        [pd.Series([1.0]), wealth.reset_index(drop=True)],
        ignore_index=True,
    ).cummax().iloc[1:]
    running_max.index = wealth.index
    drawdown = wealth / running_max - 1.0
    max_drawdown = float(drawdown.min())

    sharpe = None
    if annualized_return is not None and volatility not in (None, 0.0):
        sharpe = float((annualized_return - risk_free_rate) / volatility)

    sortino = None
    if annualized_return is not None and downside_deviation not in (None, 0.0):
        sortino = float((annualized_return - risk_free_rate) / downside_deviation)

    calmar = None
    if annualized_return is not None and max_drawdown not in (None, 0.0):
        calmar = float(annualized_return / abs(max_drawdown))

    var_95 = float(np.percentile(clean, 5)) if observation_count >= 60 else None
    var_99 = float(np.percentile(clean, 1)) if observation_count >= 60 else None

    missing_reasons: list[str] = []
    if annualized_return is None:
        missing_reasons.append("Annualized return requires more than one return observation.")
    if sharpe is None:
        missing_reasons.append("Sharpe Ratio requires non-zero volatility and annualized return.")
    if var_95 is None:
        missing_reasons.append("Historical VaR requires at least 60 return observations.")

    series_df = pd.DataFrame(
        {
            "return": clean.values,
            "cumulative_return": cumulative_return.values,
            "drawdown": drawdown.values,
        }
    )
    if dates is not None:
        valid_dates = dates.loc[clean.index] if hasattr(dates, "loc") else None
        if valid_dates is not None:
            series_df["date"] = pd.to_datetime(valid_dates.values, errors="coerce")

    return {
        "total_return": _safe_float(total_return),
        "annualized_return": _safe_float(annualized_return),
        "annualized_volatility": _safe_float(volatility),
        "downside_deviation": _safe_float(downside_deviation),
        "max_drawdown": _safe_float(max_drawdown),
        "sharpe_ratio": _safe_float(sharpe),
        "sortino_ratio": _safe_float(sortino),
        "calmar_ratio": _safe_float(calmar),
        "historical_var_95": _safe_float(var_95),
        "historical_var_99": _safe_float(var_99),
        "observation_count": observation_count,
        "data_sufficiency": _data_sufficiency(observation_count),
        "missing_reasons": missing_reasons,
    }, series_df


def _overall_risk_level(summary: dict[str, Any]) -> str:
    order = {"UNKNOWN": 0, "LOW": 1, "MODERATE": 2, "HIGH": 3, "VERY HIGH": 4}
    drawdown_level = _risk_drawdown(summary.get("max_drawdown"))
    volatility_level = _risk_volatility(summary.get("annualized_volatility"))
    return max([drawdown_level, volatility_level], key=lambda item: order[item])


def _add_metric_rules(audit: RuleAuditLog, has_returns: bool, summary: dict[str, Any], multi_asset: bool, has_weights: bool) -> None:
    if has_returns:
        audit.add("METRIC-002", "metric_calculation", "Return series exists.", "Calculate cumulative return series.", "Cumulative return calculated.")
        audit.add("METRIC-003", "metric_calculation", "Return or price series exists.", "Calculate total return.", f"total_return={summary.get('total_return')}.")
        audit.add("METRIC-004", "metric_calculation", "More than one return observation exists.", "Calculate annualized return.", f"annualized_return={summary.get('annualized_return')}.")
        audit.add("METRIC-005", "metric_calculation", "Return series exists.", "Calculate annualized volatility.", f"annualized_volatility={summary.get('annualized_volatility')}.")
        audit.add("METRIC-006", "metric_calculation", "Return series exists.", "Calculate downside deviation.", f"downside_deviation={summary.get('downside_deviation')}.")
        audit.add("METRIC-007", "metric_calculation", "Return series exists.", "Calculate maximum drawdown.", f"max_drawdown={summary.get('max_drawdown')}.")
        audit.add("METRIC-009", "metric_calculation", "Annualized return and non-zero volatility are available.", "Calculate Sharpe Ratio when possible.", f"sharpe_ratio={summary.get('sharpe_ratio')}.")
        audit.add("METRIC-010", "metric_calculation", "Annualized return and downside deviation are available.", "Calculate Sortino Ratio when possible.", f"sortino_ratio={summary.get('sortino_ratio')}.")
        audit.add("METRIC-011", "metric_calculation", "Annualized return and max drawdown are available.", "Calculate Calmar Ratio when possible.", f"calmar_ratio={summary.get('calmar_ratio')}.")
        if summary.get("historical_var_95") is not None:
            audit.add("METRIC-008", "metric_calculation", "At least 60 return observations exist.", "Calculate historical VaR approximation.", f"VaR95={summary.get('historical_var_95')}.")
    if multi_asset:
        audit.add("METRIC-012", "metric_calculation", "Asset column exists.", "Calculate asset-level metric table.", "Asset metrics generated.")
        audit.add("METRIC-013", "metric_calculation", "Two or more asset return series exist.", "Calculate Pearson correlation matrix.", "Correlation matrix generated when overlap is sufficient.")
    if has_weights:
        audit.add("METRIC-015", "metric_calculation", "Weight column exists.", "Calculate max weight and HHI concentration.", "Concentration metrics generated.")
    audit.add("RISK-001", "risk_classification", "Maximum drawdown is available.", "Classify drawdown risk.", f"drawdown_risk={summary.get('drawdown_risk_level')}.")
    audit.add("RISK-002", "risk_classification", "Annualized volatility is available.", "Classify volatility risk.", f"volatility_risk={summary.get('volatility_risk_level')}.")
    audit.add("RISK-003", "risk_classification", "Sharpe Ratio is available when calculable.", "Classify risk-adjusted performance.", f"sharpe_quality={summary.get('sharpe_quality')}.")
    audit.add("RISK-004", "risk_classification", "Observation count is available.", "Classify data sufficiency.", f"data_sufficiency={summary.get('data_sufficiency')}.")


def _asset_metric_table(returns_df: pd.DataFrame, periods_per_year: int, risk_free_rate: float) -> tuple[list[dict[str, Any]], pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, Any]] = []
    cumulative_parts: list[pd.DataFrame] = []
    drawdown_parts: list[pd.DataFrame] = []

    for asset, group in returns_df.groupby("asset"):
        metrics, series = _series_metrics(
            group["return"],
            group["date"] if "date" in group.columns else None,
            periods_per_year,
            risk_free_rate,
        )
        row = {"asset": asset, **metrics}
        row["drawdown_risk_level"] = _risk_drawdown(metrics.get("max_drawdown"))
        row["volatility_risk_level"] = _risk_volatility(metrics.get("annualized_volatility"))
        row["sharpe_quality"] = _sharpe_quality(metrics.get("sharpe_ratio"))
        rows.append(row)
        if not series.empty:
            series = series.copy()
            series["asset"] = asset
            cumulative_parts.append(series[[column for column in ["date", "asset", "cumulative_return"] if column in series.columns]])
            drawdown_parts.append(series[[column for column in ["date", "asset", "drawdown"] if column in series.columns]])

    cumulative_df = pd.concat(cumulative_parts, ignore_index=True) if cumulative_parts else pd.DataFrame()
    drawdown_df = pd.concat(drawdown_parts, ignore_index=True) if drawdown_parts else pd.DataFrame()
    return rows, cumulative_df, drawdown_df


def _correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in returns_df.columns or "asset" not in returns_df.columns:
        return pd.DataFrame()
    wide = returns_df.pivot_table(index="date", columns="asset", values="return", aggfunc="last")
    if wide.shape[1] < 2:
        return pd.DataFrame()
    return wide.corr()


def _portfolio_return_source(returns_df: pd.DataFrame) -> pd.Series:
    if "date" not in returns_df.columns:
        return returns_df["return"]

    if "weight" not in returns_df.columns:
        return returns_df.groupby("date", dropna=False)["return"].mean()

    working = returns_df.copy()
    working["weight"] = pd.to_numeric(working["weight"], errors="coerce")
    working["return"] = pd.to_numeric(working["return"], errors="coerce")

    def _weighted(group: pd.DataFrame) -> float:
        valid = group.dropna(subset=["return"])
        if valid.empty:
            return np.nan
        weights = valid["weight"].fillna(0.0)
        total_weight = float(weights.sum())
        if total_weight <= 0:
            return float(valid["return"].mean())
        return float((valid["return"] * weights / total_weight).sum())

    return working.groupby("date", dropna=False).apply(_weighted, include_groups=False)


def _allocation_metrics(std_df: pd.DataFrame) -> dict[str, Any]:
    if "weight" not in std_df.columns:
        return {}
    weights = pd.to_numeric(std_df["weight"], errors="coerce").dropna()
    if weights.empty:
        return {}
    max_weight = float(weights.max())
    hhi = float(np.square(weights).sum())
    return {
        "max_weight": max_weight,
        "hhi": hhi,
        "concentration_level": "HIGH" if max_weight > 0.5 or hhi > 0.25 else "MODERATE" if max_weight > 0.35 else "LOW",
    }


def compute_metrics(
    std_df: pd.DataFrame,
    schema: dict[str, Any],
    risk_free_rate: float = 0.0,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute return, risk, and multi-asset metrics according to metric rules."""

    audit = RuleAuditLog()
    periods = _periods_per_year(profile)
    audit.add(
        rule_id="METRIC-BASE-002",
        step="metric_assumption",
        condition="Frequency-derived periods_per_year is required for annualized metrics.",
        action="Use profile periods_per_year or default daily value.",
        result=f"periods_per_year={periods}.",
    )
    audit.add(
        rule_id="METRIC-BASE-003",
        step="metric_assumption",
        condition="Risk-free rate is used for risk-adjusted return metrics.",
        action="Use user input or default 0.0.",
        result=f"risk_free_rate={risk_free_rate:.2%}.",
    )

    if std_df.empty:
        return {
            "summary": {"risk_level": "UNKNOWN", "missing_reasons": ["No standardized dataframe available."]},
            "asset_metrics": [],
            "returns": pd.DataFrame(),
            "cumulative_returns": pd.DataFrame(),
            "drawdowns": pd.DataFrame(),
            "correlation_matrix": pd.DataFrame(),
            "allocation": {},
            "applied_rules": audit.to_records(),
        }

    allocation = _allocation_metrics(std_df)
    schema_type = str(schema.get("schema_type", "unknown"))
    returns_df = pd.DataFrame() if schema_type == "allocation" else _returns_from_standardized(std_df, audit)

    if returns_df.empty:
        reason = (
            "Allocation or holdings snapshot does not provide historical return observations."
            if schema_type == "allocation"
            else "No price or return field available for time-series metrics."
        )
        summary = {
            "risk_level": "UNKNOWN",
            "missing_reasons": [reason],
            "allocation": allocation,
            "risk_free_rate": risk_free_rate,
        }
        _add_metric_rules(audit, False, summary, False, bool(allocation))
        return {
            "summary": summary,
            "asset_metrics": [],
            "returns": returns_df,
            "cumulative_returns": pd.DataFrame(),
            "drawdowns": pd.DataFrame(),
            "correlation_matrix": pd.DataFrame(),
            "allocation": allocation,
            "applied_rules": audit.to_records(),
        }

    multi_asset = returns_df["asset"].nunique(dropna=True) > 1
    if multi_asset:
        asset_metrics, cumulative_df, drawdown_df = _asset_metric_table(returns_df, periods, risk_free_rate)
        summary_source = _portfolio_return_source(returns_df)
        dates = summary_source.index.to_series() if "date" in returns_df.columns else None
        summary, _ = _series_metrics(summary_source, dates, periods, risk_free_rate)
        correlation = _correlation_matrix(returns_df)
    else:
        summary, series = _series_metrics(
            returns_df["return"],
            returns_df["date"] if "date" in returns_df.columns else None,
            periods,
            risk_free_rate,
        )
        asset_metrics = []
        if not returns_df.empty:
            asset_name = returns_df["asset"].dropna().iloc[0] if returns_df["asset"].notna().any() else "Portfolio"
            asset_row = {"asset": asset_name, **summary}
            asset_metrics.append(asset_row)
        cumulative_df = series.copy()
        drawdown_df = series.copy()
        if not cumulative_df.empty:
            cumulative_df["asset"] = returns_df["asset"].dropna().iloc[0] if returns_df["asset"].notna().any() else "Portfolio"
            drawdown_df["asset"] = cumulative_df["asset"]
        correlation = pd.DataFrame()

    summary["drawdown_risk_level"] = _risk_drawdown(summary.get("max_drawdown"))
    summary["volatility_risk_level"] = _risk_volatility(summary.get("annualized_volatility"))
    summary["sharpe_quality"] = _sharpe_quality(summary.get("sharpe_ratio"))
    summary["risk_level"] = _overall_risk_level(summary)
    summary["allocation"] = allocation
    summary["risk_free_rate"] = risk_free_rate

    _add_metric_rules(audit, True, summary, multi_asset, bool(allocation))

    return {
        "summary": summary,
        "asset_metrics": asset_metrics,
        "returns": returns_df,
        "cumulative_returns": cumulative_df,
        "drawdowns": drawdown_df,
        "correlation_matrix": correlation,
        "allocation": allocation,
        "applied_rules": audit.to_records(),
    }


def format_percent(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2%}"


def format_ratio(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"
