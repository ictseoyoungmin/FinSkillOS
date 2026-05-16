"""Schema inference and standardization for FinSkillOS.

Implements AUTO-CONTRACT-003 and the DATA/SCHEMA behavior described in
`FinSkillOS_skills/skills/01_data_understanding.md`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from engine.rule_engine import AppliedRule, RuleAuditLog


FIELD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "date": ("date", "dt", "datetime", "timestamp", "time", "일자", "날짜", "기준일", "거래일", "평가일"),
    "asset": ("asset", "ticker", "symbol", "code", "name", "fund", "product", "종목", "티커", "자산", "펀드", "상품", "코드"),
    "price": ("adj_close", "adjusted", "close", "price", "nav", "value", "index", "level", "종가", "가격", "기준가", "지수", "평가금액"),
    "return": ("return", "ret", "yield", "pct", "change", "수익률", "등락률", "변화율"),
    "volume": ("volume", "amount", "turnover", "거래량", "거래대금", "금액"),
    "weight": ("weight", "allocation", "ratio", "비중", "배분", "구성비"),
    "sector": ("sector", "industry", "class", "type", "category", "섹터", "업종", "자산군", "유형"),
    "region": ("region", "country", "지역", "국가"),
}

RULE_IDS = {
    "date": "DATA-001",
    "asset": "DATA-002",
    "price": "DATA-003",
    "return": "DATA-004",
    "volume": "DATA-005",
    "weight": "DATA-006",
    "sector": "DATA-007",
    "region": "DATA-007",
}


@dataclass(frozen=True)
class MappingCandidate:
    field: str
    source: str
    confidence: float
    rule_id: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _keyword_score(column: str, field: str) -> float:
    lowered = column.lower()
    keywords = FIELD_KEYWORDS[field]
    if lowered == field:
        return 1.0
    if lowered in keywords:
        return 0.95
    if any(keyword.lower() == lowered for keyword in keywords):
        return 0.95
    if any(keyword.lower() in lowered for keyword in keywords):
        return 0.85
    return 0.0


def _dtype_score(series: pd.Series, field: str) -> float:
    is_numeric = pd.api.types.is_numeric_dtype(series)
    is_text = pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series)
    if field == "date":
        parsed = pd.to_datetime(series, errors="coerce")
        non_null = series.dropna()
        if non_null.empty:
            return 0.0
        return float(parsed.notna().sum() / len(non_null))
    if field in {"price", "return", "volume", "weight"}:
        return 1.0 if is_numeric else 0.0
    if field in {"asset", "sector", "region"}:
        return 1.0 if is_text else 0.5 if not is_numeric else 0.0
    return 0.0


def _distribution_score(series: pd.Series, field: str, row_count: int) -> float:
    non_null = series.dropna()
    if non_null.empty:
        return 0.0
    if field == "date":
        parsed = pd.to_datetime(series, errors="coerce")
        return float(parsed.notna().sum() / len(non_null))
    if field == "asset":
        unique_ratio = non_null.nunique(dropna=True) / max(row_count, 1)
        if row_count <= 10:
            return 0.8 if non_null.nunique(dropna=True) >= 1 else 0.0
        return 1.0 if unique_ratio <= 0.5 else 0.3
    if field == "price":
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if numeric.empty:
            return 0.0
        positive_ratio = float((numeric > 0).mean())
        return positive_ratio
    if field == "return":
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if numeric.empty:
            return 0.0
        in_decimal_range = float(numeric.between(-1, 1).mean())
        near_zero_mean = 1.0 if abs(float(numeric.mean())) < 0.1 else 0.5
        return 0.7 * in_decimal_range + 0.3 * near_zero_mean
    if field == "volume":
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if numeric.empty:
            return 0.0
        return float((numeric >= 0).mean())
    if field == "weight":
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if numeric.empty:
            return 0.0
        total = float(numeric.sum())
        if abs(total - 1.0) <= 0.05 or abs(total - 100.0) <= 5:
            return 1.0
        if numeric.between(0, 1).mean() >= 0.8:
            return 0.8
        return 0.2
    if field in {"sector", "region"}:
        unique_ratio = non_null.nunique(dropna=True) / max(row_count, 1)
        return 1.0 if unique_ratio <= 0.7 else 0.4
    return 0.0


def _missingness_score(series: pd.Series) -> float:
    return float(1.0 - series.isna().mean())


def _confidence(df: pd.DataFrame, column: str, field: str) -> tuple[float, str]:
    series = df[column]
    name_match = _keyword_score(column, field)
    dtype = _dtype_score(series, field)
    distribution = _distribution_score(series, field, len(df))
    missingness = _missingness_score(series)
    confidence = 0.4 * name_match + 0.3 * dtype + 0.2 * distribution + 0.1 * missingness
    reason = (
        f"name={name_match:.2f}, dtype={dtype:.2f}, "
        f"distribution={distribution:.2f}, missingness={missingness:.2f}"
    )
    return round(float(confidence), 4), reason


def _status(confidence: float) -> str:
    if confidence >= 0.9:
        return "auto_high"
    if confidence >= 0.7:
        return "auto_review"
    if confidence >= 0.5:
        return "candidate"
    return "low"


def _best_candidate(df: pd.DataFrame, field: str, exclude: set[str]) -> MappingCandidate | None:
    candidates: list[MappingCandidate] = []
    for column in df.columns:
        if column in exclude:
            continue
        confidence, reason = _confidence(df, column, field)
        if confidence >= 0.5:
            candidates.append(
                MappingCandidate(
                    field=field,
                    source=column,
                    confidence=confidence,
                    rule_id=RULE_IDS[field],
                    status=_status(confidence),
                    reason=reason,
                )
            )
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (-item.confidence, item.source))[0]


def _mapping_dict(candidates: list[MappingCandidate]) -> dict[str, dict[str, Any]]:
    return {
        candidate.field: {
            "source": candidate.source,
            "confidence": candidate.confidence,
            "rule_id": candidate.rule_id,
            "status": candidate.status,
            "reason": candidate.reason,
        }
        for candidate in candidates
    }


def _schema_type(df: pd.DataFrame, mapping: dict[str, dict[str, Any]]) -> str:
    has_date = "date" in mapping
    has_asset = "asset" in mapping
    has_price_or_return = "price" in mapping or "return" in mapping
    has_weight = "weight" in mapping
    numeric_columns = [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]

    source_names = {str(details.get("source", "")).lower() for details in mapping.values()}
    all_names = {str(column).lower() for column in df.columns} | source_names
    holdings_markers = {
        "quantity",
        "avg_buy_price",
        "current_price",
        "market_value",
        "cost_basis",
        "unrealized_pnl",
        "unrealized_return",
        "portfolio_weight",
        "effective_exposure",
    }
    looks_like_holdings = has_weight and has_asset and any(
        any(marker in name for marker in holdings_markers) for name in all_names
    )
    if looks_like_holdings:
        return "allocation"
    if has_weight and "asset" in mapping and not has_date:
        return "allocation"
    if has_date and not has_asset and len(numeric_columns) >= 2:
        mapped_numeric = {value["source"] for key, value in mapping.items() if key in {"price", "return", "volume", "weight"}}
        wide_numeric = [column for column in numeric_columns if column not in mapped_numeric]
        if len(wide_numeric) >= 2:
            return "multi_asset_wide"
    if has_date and has_asset and has_price_or_return:
        return "multi_asset_long"
    if has_date and has_price_or_return:
        return "single_asset_price" if "price" in mapping else "single_asset_return"
    if has_weight and "asset" in mapping:
        return "allocation"
    return "unknown"


def _standardize(df: pd.DataFrame, schema_type: str, mapping: dict[str, dict[str, Any]], audit: RuleAuditLog) -> pd.DataFrame:
    if schema_type == "multi_asset_wide":
        date_source = mapping["date"]["source"]
        numeric_columns = [column for column in df.columns if pd.api.types.is_numeric_dtype(df[column])]
        mapped_non_assets = {
            value["source"]
            for field, value in mapping.items()
            if field in {"volume", "weight"} and value["source"] in numeric_columns
        }
        asset_columns = [column for column in numeric_columns if column not in mapped_non_assets]
        standardized = df[[date_source] + asset_columns].melt(
            id_vars=[date_source],
            value_vars=asset_columns,
            var_name="asset",
            value_name="price",
        )
        standardized = standardized.rename(columns={date_source: "date"})
        audit.add(
            rule_id="DATA-STRUCT-003",
            step="schema_standardization",
            condition="Date column exists and multiple numeric columns can be treated as asset series.",
            action="Melt wide format into long format.",
            result=f"{len(asset_columns)} asset column(s) converted to `date, asset, price`.",
        )
        return standardized

    rename_map = {details["source"]: field for field, details in mapping.items()}
    keep_sources = [details["source"] for details in mapping.values()]
    standardized = df[keep_sources].rename(columns=rename_map).copy()

    if "date" in standardized.columns:
        standardized["date"] = pd.to_datetime(standardized["date"], errors="coerce")
        standardized = standardized.sort_values(["date"] + (["asset"] if "asset" in standardized.columns else []))
        audit.add(
            rule_id="DATA-QA-005",
            step="schema_standardization",
            condition="Time-series data should be processed in ascending date order.",
            action="Sort standardized dataframe by date.",
            result="Standardized dataframe sorted by date.",
        )

    if "weight" in standardized.columns:
        total = pd.to_numeric(standardized["weight"], errors="coerce").sum()
        if abs(float(total) - 100.0) <= 5:
            standardized["weight"] = pd.to_numeric(standardized["weight"], errors="coerce") / 100.0
            audit.add(
                rule_id="DATA-006",
                step="schema_standardization",
                condition="Weight column sum is close to 100.",
                action="Normalize weights to 0-1 scale.",
                result="Weight values divided by 100.",
            )

    return standardized


def _add_mapping_rules(audit: RuleAuditLog, candidates: list[MappingCandidate]) -> None:
    for candidate in candidates:
        audit.add(
            rule_id=candidate.rule_id,
            step="schema_mapping",
            condition=f"`{candidate.source}` matched `{candidate.field}` with confidence {candidate.confidence:.2f}.",
            action=f"Map source column `{candidate.source}` to standard field `{candidate.field}`.",
            result=f"{candidate.field} <- {candidate.source} ({candidate.status}).",
        )


def infer_schema(df: pd.DataFrame, profile: dict[str, Any], mode: str = "Auto") -> dict[str, Any]:
    """Map arbitrary input columns to the FinSkillOS standard schema."""

    audit = RuleAuditLog()
    selected: list[MappingCandidate] = []
    used_sources: set[str] = set()

    if profile.get("date_candidates"):
        top_date = profile["date_candidates"][0]
        confidence = max(float(top_date["score"]), _confidence(df, top_date["column"], "date")[0])
        selected.append(
            MappingCandidate(
                field="date",
                source=top_date["column"],
                confidence=round(confidence, 4),
                rule_id="DATA-001",
                status=_status(confidence),
                reason=top_date.get("reason", "profile date candidate"),
            )
        )
        used_sources.add(top_date["column"])

    for field in ("asset", "price", "return", "volume", "weight", "sector", "region"):
        candidate = _best_candidate(df, field, used_sources)
        if candidate and candidate.confidence >= 0.7:
            selected.append(candidate)
            used_sources.add(candidate.source)

    mapping = _mapping_dict(selected)
    schema_type = _schema_type(df, mapping)

    if schema_type == "multi_asset_wide":
        # Wide format uses numeric column names as assets; remove single price mapping if it blocks clarity.
        mapping = {field: details for field, details in mapping.items() if field not in {"price", "return"}}
        selected = [
            candidate for candidate in selected if candidate.field not in {"price", "return"}
        ]

    _add_mapping_rules(audit, selected)
    audit.add(
        rule_id="SCHEMA-001",
        step="schema_mapping",
        condition="Candidate source columns were scored against FinSkillOS standard fields.",
        action="Build the standard schema mapping table.",
        result=f"{len(selected)} standard field mapping(s) selected.",
        severity="WARNING" if not selected else "INFO",
    )

    structure_rule = {
        "single_asset_price": "DATA-STRUCT-001",
        "single_asset_return": "DATA-STRUCT-001",
        "multi_asset_long": "DATA-STRUCT-002",
        "multi_asset_wide": "DATA-STRUCT-003",
        "allocation": "DATA-STRUCT-004",
        "unknown": "DATA-STRUCT-UNKNOWN",
    }[schema_type]
    audit.add(
        rule_id=structure_rule,
        step="schema_classification",
        condition="Standard field availability was evaluated.",
        action=f"Classify dataset as `{schema_type}`.",
        result=f"Detected schema type: {schema_type}.",
        severity="WARNING" if schema_type == "unknown" else "INFO",
    )

    standardized_df = _standardize(df, schema_type, mapping, audit) if schema_type != "unknown" else pd.DataFrame()

    return {
        "schema_type": schema_type,
        "mapping": mapping,
        "standardized_df": standardized_df,
        "mapping_table": [candidate.to_dict() for candidate in selected],
        "applied_rules": audit.to_records(),
        "mode": mode,
    }
