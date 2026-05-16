"""Data profiling rules for FinSkillOS.

This module implements the Slice 3 contract from
`FinSkillOS_skills/skills/05_vibecoding_automation.md` and the relevant DATA
rules from `FinSkillOS_skills/skills/01_data_understanding.md`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import warnings

import numpy as np
import pandas as pd

from engine.rule_engine import AppliedRule, RuleAuditLog


DATE_KEYWORDS = (
    "date",
    "dt",
    "datetime",
    "timestamp",
    "time",
    "일자",
    "날짜",
    "기준일",
    "거래일",
    "평가일",
)


@dataclass(frozen=True)
class ColumnCandidate:
    column: str
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _has_keyword(column: str, keywords: tuple[str, ...]) -> bool:
    lowered = column.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _parse_datetime_ratio(series: pd.Series) -> tuple[float, pd.Series]:
    non_null = series.dropna()
    if non_null.empty:
        return 0.0, pd.Series(pd.NaT, index=series.index)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(series, errors="coerce")
    ratio = float(parsed.notna().sum() / len(non_null))
    return ratio, parsed


def _missing_rates(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {column: 0.0 for column in df.columns}
    return {column: float(rate) for column, rate in df.isna().mean().items()}


def _column_type_groups(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    numeric_columns = [
        column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])
    ]
    categorical_columns = [
        column
        for column in df.columns
        if column not in numeric_columns
        and (
            pd.api.types.is_string_dtype(df[column])
            or pd.api.types.is_categorical_dtype(df[column])
            or pd.api.types.is_object_dtype(df[column])
        )
    ]
    return numeric_columns, categorical_columns


def _date_candidates(df: pd.DataFrame, missing_rates: dict[str, float]) -> list[ColumnCandidate]:
    candidates: list[ColumnCandidate] = []
    for column in df.columns:
        keyword_match = _has_keyword(column, DATE_KEYWORDS)
        parse_ratio = 0.0
        if pd.api.types.is_numeric_dtype(df[column]) and not keyword_match:
            numeric_values = pd.to_numeric(df[column], errors="coerce").dropna()
            if not numeric_values.empty:
                date_code_like = numeric_values.between(19000101, 21001231).mean() >= 0.8
                if date_code_like:
                    parse_ratio, _ = _parse_datetime_ratio(numeric_values.astype("Int64").astype(str))
        else:
            parse_ratio, _ = _parse_datetime_ratio(df[column])
        if parse_ratio >= 0.8 or keyword_match:
            score = 0.75 * parse_ratio + 0.25 * float(keyword_match)
            missing_penalty = missing_rates.get(column, 0.0) * 0.1
            score = max(0.0, min(1.0, score - missing_penalty))
            reason_parts = []
            if parse_ratio >= 0.8:
                reason_parts.append(f"{parse_ratio:.0%} datetime parse success")
            if keyword_match:
                reason_parts.append("date keyword match")
            candidates.append(
                ColumnCandidate(
                    column=column,
                    score=round(score, 4),
                    reason=", ".join(reason_parts),
                )
            )
    return sorted(candidates, key=lambda item: (-item.score, missing_rates.get(item.column, 0.0)))


def _detect_frequency(parsed_dates: pd.Series) -> tuple[str, int, AppliedRule]:
    unique_dates = parsed_dates.dropna().drop_duplicates().sort_values()
    if len(unique_dates) < 2:
        return (
            "unknown",
            252,
            AppliedRule(
                rule_id="DATA-FREQ-004",
                step="frequency_detection",
                condition="Fewer than two parsed dates are available.",
                action="Use unknown frequency fallback.",
                result="Frequency unknown; periods_per_year defaults to 252 with warning.",
                severity="WARNING",
            ),
        )

    median_days = float(unique_dates.diff().dt.days.dropna().median())
    if 1 <= median_days <= 3:
        return (
            "daily",
            252,
            AppliedRule(
                rule_id="DATA-FREQ-001",
                step="frequency_detection",
                condition="Median date gap is between 1 and 3 days.",
                action="Classify frequency as daily.",
                result="periods_per_year=252.",
            ),
        )
    if 5 <= median_days <= 9:
        return (
            "weekly",
            52,
            AppliedRule(
                rule_id="DATA-FREQ-002",
                step="frequency_detection",
                condition="Median date gap is between 5 and 9 days.",
                action="Classify frequency as weekly.",
                result="periods_per_year=52.",
            ),
        )
    if 25 <= median_days <= 35:
        return (
            "monthly",
            12,
            AppliedRule(
                rule_id="DATA-FREQ-003",
                step="frequency_detection",
                condition="Median date gap is between 25 and 35 days.",
                action="Classify frequency as monthly.",
                result="periods_per_year=12.",
            ),
        )
    return (
        "unknown",
        252,
        AppliedRule(
            rule_id="DATA-FREQ-004",
            step="frequency_detection",
            condition=f"Median date gap is {median_days:.1f} days.",
            action="Use unknown frequency fallback.",
            result="Frequency unknown; periods_per_year defaults to 252 with warning.",
            severity="WARNING",
        ),
    )


def _quality_warnings(
    df: pd.DataFrame,
    date_candidates: list[ColumnCandidate],
    missing_rates: dict[str, float],
) -> tuple[list[dict[str, Any]], list[AppliedRule], str, int]:
    warnings: list[dict[str, Any]] = []
    rules: list[AppliedRule] = []
    frequency = "none"
    periods_per_year = 0

    high_missing_columns = [
        column for column, rate in missing_rates.items() if rate > 0.2
    ]
    if high_missing_columns:
        for column in high_missing_columns:
            warnings.append(
                {
                    "rule_id": "DATA-QA-001",
                    "severity": "WARNING",
                    "message": f"Column `{column}` has {missing_rates[column]:.1%} missing values.",
                    "column": column,
                }
            )
        rules.append(
            AppliedRule(
                rule_id="DATA-QA-001",
                step="data_quality",
                condition="One or more columns have missing value rate above 20%.",
                action="Expose data quality warnings.",
                result=f"{len(high_missing_columns)} high-missing column(s) detected.",
                severity="WARNING",
            )
        )
    else:
        rules.append(
            AppliedRule(
                rule_id="DATA-QA-001",
                step="data_quality",
                condition="Column missing rates were calculated.",
                action="Check whether any column exceeds the 20% warning threshold.",
                result="No high-missing columns detected.",
            )
        )

    if date_candidates:
        date_column = date_candidates[0].column
        _, parsed_dates = _parse_datetime_ratio(df[date_column])
        if parsed_dates.notna().sum() < 60:
            warnings.append(
                {
                    "rule_id": "DATA-QA-003",
                    "severity": "WARNING",
                    "message": "Time-series observations are below 60; annualized metrics may be unstable.",
                    "column": date_column,
                }
            )
            rules.append(
                AppliedRule(
                    rule_id="DATA-QA-003",
                    step="data_quality",
                    condition="Parsed time-series observation count is below 60.",
                    action="Add insufficient history warning.",
                    result=f"{int(parsed_dates.notna().sum())} parsed dates detected.",
                    severity="WARNING",
                )
            )

        non_null_dates = parsed_dates.dropna()
        if len(non_null_dates) >= 2 and not non_null_dates.is_monotonic_increasing:
            warnings.append(
                {
                    "rule_id": "DATA-QA-005",
                    "severity": "INFO",
                    "message": f"Date column `{date_column}` is not sorted ascending; downstream schema mapping should sort it.",
                    "column": date_column,
                }
            )
            rules.append(
                AppliedRule(
                    rule_id="DATA-QA-005",
                    step="data_quality",
                    condition="Parsed date values are not monotonic increasing.",
                    action="Record that downstream processing should sort by date.",
                    result=f"`{date_column}` requires date sorting.",
                )
            )

        frequency, periods_per_year, frequency_rule = _detect_frequency(parsed_dates)
        rules.append(frequency_rule)
        if frequency == "unknown":
            warnings.append(
                {
                    "rule_id": "DATA-FREQ-004",
                    "severity": "WARNING",
                    "message": "Frequency could not be detected reliably; daily annualization fallback will be used.",
                    "column": date_column,
                }
            )
    else:
        frequency = "none"
        periods_per_year = 0
        warnings.append(
            {
                "rule_id": "DATA-001",
                "severity": "WARNING",
                "message": "No date column candidate was detected; time-series analysis should be disabled.",
                "column": None,
            }
        )

    return warnings, rules, frequency, periods_per_year


def _extreme_return_warnings(df: pd.DataFrame, numeric_columns: list[str]) -> tuple[list[dict[str, Any]], list[AppliedRule]]:
    warnings: list[dict[str, Any]] = []
    rules: list[AppliedRule] = []
    flagged: list[str] = []

    for column in numeric_columns:
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(series) < 3 or (series <= 0).mean() > 0.1:
            continue
        returns = series.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        if returns.abs().gt(0.5).any():
            flagged.append(column)
            warnings.append(
                {
                    "rule_id": "DATA-QA-004",
                    "severity": "WARNING",
                    "message": f"Column `{column}` has at least one period change above 50%.",
                    "column": column,
                }
            )

    if flagged:
        rules.append(
            AppliedRule(
                rule_id="DATA-QA-004",
                step="data_quality",
                condition="One or more numeric series have period changes above 50%.",
                action="Flag extreme return candidates without removing rows.",
                result=", ".join(flagged),
                severity="WARNING",
            )
        )
    return warnings, rules


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Detect row count, column types, missingness, and date/numeric candidates."""

    audit = RuleAuditLog()
    row_count = int(len(df))
    column_count = int(len(df.columns))
    missing_rates = _missing_rates(df)
    numeric_columns, categorical_columns = _column_type_groups(df)
    date_candidates = _date_candidates(df, missing_rates)

    if date_candidates:
        audit.add(
            rule_id="DATA-001",
            step="column_type_inference",
            condition="A column has at least 80% datetime parse success or a date keyword match.",
            action="Classify matching columns as date candidates.",
            result=f"Top date candidate: `{date_candidates[0].column}`.",
        )
    else:
        audit.add(
            rule_id="DATA-001",
            step="column_type_inference",
            condition="No column reached the date parse or keyword threshold.",
            action="Disable time-series assumptions until manual mapping or static analysis is available.",
            result="No date candidate detected.",
            severity="WARNING",
        )

    warnings, quality_rules, frequency, periods_per_year = _quality_warnings(
        df=df,
        date_candidates=date_candidates,
        missing_rates=missing_rates,
    )
    audit.extend(quality_rules)

    extreme_warnings, extreme_rules = _extreme_return_warnings(df, numeric_columns)
    warnings.extend(extreme_warnings)
    audit.extend(extreme_rules)

    return {
        "row_count": row_count,
        "column_count": column_count,
        "missing_rates": missing_rates,
        "date_candidates": [candidate.to_dict() for candidate in date_candidates],
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "quality_warnings": warnings,
        "frequency": frequency,
        "periods_per_year": periods_per_year,
        "applied_rules": audit.to_records(),
    }
