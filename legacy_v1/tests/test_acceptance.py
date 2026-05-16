from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

from engine.chart_planner import plan_charts
from engine.data_profiler import profile_dataframe
from engine.history_enricher import fetch_history_for_holdings, is_holdings_snapshot
import engine.history_enricher as history_enricher
from engine.insight_engine import _contains_forbidden, _safe_insight, generate_insights
from engine.metrics import compute_metrics
from engine.report_builder import build_html_report
from engine.rule_engine import RuleAuditLog
from engine.schema_mapper import infer_schema


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = ROOT / "sample_data"


def run_pipeline(sample_name: str) -> dict[str, object]:
    df = pd.read_csv(SAMPLE_DATA / sample_name)
    profile = profile_dataframe(df)
    schema = infer_schema(df, profile, mode="Auto Detect")
    metrics = compute_metrics(schema["standardized_df"], schema, profile=profile)
    chart_plan = plan_charts(schema, metrics)
    insights = generate_insights(metrics, profile, schema)

    audit = RuleAuditLog()
    audit.extend(profile["applied_rules"])
    audit.extend(schema["applied_rules"])
    audit.extend(metrics["applied_rules"])
    for chart in chart_plan:
        audit.add(
            rule_id=chart["rule_id"],
            step="chart_planning",
            condition=chart["reason"],
            action=f"Plan chart `{chart['chart_id']}`.",
            result="Selected for rendering." if chart.get("available") else "Not rendered; prerequisites are unavailable.",
        )
    audit.extend(insights["applied_rules"])

    return {
        "source_name": sample_name,
        "mode": "Auto Detect",
        "profile": profile,
        "schema": schema,
        "metrics": metrics,
        "chart_plan": chart_plan,
        "insights": insights,
        "applied_rules": audit.deduplicated_records(),
    }


class AcceptanceTests(unittest.TestCase):
    def test_upload_works_with_valid_csv_shape(self) -> None:
        result = run_pipeline("single_asset_price.csv")

        self.assertEqual(result["schema"]["schema_type"], "single_asset_price")
        self.assertGreater(result["profile"]["row_count"], 0)
        self.assertIsNotNone(result["metrics"]["summary"]["total_return"])
        self.assertGreaterEqual(len(result["insights"]["insights"]), 1)

    def test_mixed_schema_detection_maps_standard_fields(self) -> None:
        result = run_pipeline("mixed_schema_assets.csv")
        mapping = result["schema"]["mapping"]

        self.assertEqual(result["schema"]["schema_type"], "multi_asset_long")
        self.assertEqual(mapping["date"]["source"], "trade_dt")
        self.assertEqual(mapping["asset"]["source"], "ticker_name")
        self.assertEqual(mapping["price"]["source"], "nav_value")
        self.assertEqual(mapping["volume"]["source"], "trading_amount")

    def test_multi_asset_charts_are_planned(self) -> None:
        result = run_pipeline("multi_asset_portfolio.csv")
        available_chart_ids = {
            chart["chart_id"]
            for chart in result["chart_plan"]
            if chart.get("available")
        }

        self.assertIn("indexed_cumulative_return", available_chart_ids)
        self.assertIn("risk_return_scatter", available_chart_ids)
        self.assertIn("correlation_heatmap", available_chart_ids)
        self.assertTrue(result["metrics"]["asset_metrics"])

    def test_holdings_snapshot_is_allocation_not_return_series(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "ticker": "AAA",
                    "as_of_date": "2026-05-01",
                    "current_price": 100.0,
                    "unrealized_return": 0.05,
                    "effective_exposure_weight": 0.65,
                    "quantity": 10,
                    "market_value_net": 1000.0,
                },
                {
                    "ticker": "BBB",
                    "as_of_date": "2026-05-01",
                    "current_price": 50.0,
                    "unrealized_return": -0.02,
                    "effective_exposure_weight": 0.35,
                    "quantity": 20,
                    "market_value_net": 1000.0,
                },
            ]
        )
        profile = profile_dataframe(df)
        schema = infer_schema(df, profile, mode="Auto Detect")
        metrics = compute_metrics(schema["standardized_df"], schema, profile=profile)

        self.assertEqual(schema["schema_type"], "allocation")
        self.assertTrue(metrics["returns"].empty)
        self.assertEqual(metrics["summary"]["allocation"]["concentration_level"], "HIGH")
        self.assertIn("holdings snapshot", metrics["summary"]["missing_reasons"][0])

    def test_holdings_snapshot_can_expand_to_price_history(self) -> None:
        class FakeTicker:
            def __init__(self, ticker: str) -> None:
                self.ticker = ticker

            def history(self, start: str, end: str, interval: str, auto_adjust: bool) -> pd.DataFrame:
                return pd.DataFrame(
                    {
                        "Date": pd.date_range("2026-01-01", periods=6, freq="D"),
                        "Close": [100, 101, 102, 103, 104, 105],
                        "Adj Close": [100, 101, 102, 103, 104, 105],
                    }
                )

        class FakeYf:
            Ticker = FakeTicker

        original_yf = history_enricher.yf
        history_enricher.yf = FakeYf()
        try:
            holdings = pd.DataFrame(
                [
                    {"ticker": "AAA", "yahoo_ticker": "AAA", "quantity": 10, "effective_exposure_weight": 0.6, "market_value_net": 600},
                    {"ticker": "BBB", "yahoo_ticker": "BBB", "quantity": 20, "effective_exposure_weight": 0.4, "market_value_net": 400},
                ]
            )
            history, log = fetch_history_for_holdings(holdings)
        finally:
            history_enricher.yf = original_yf

        self.assertTrue(is_holdings_snapshot(holdings))
        self.assertEqual(len(history), 12)
        self.assertEqual(set(history["asset"]), {"AAA", "BBB"})
        self.assertTrue({"date", "asset", "price", "weight"}.issubset(history.columns))
        self.assertEqual(set(log["status"]), {"ok"})

    def test_forbidden_advice_is_blocked_from_insights_and_report(self) -> None:
        unsafe = {
            "category": "return",
            "severity": "INFO",
            "fact": "이 자산을 매수하세요.",
            "interpretation": "Guaranteed profit is not an acceptable message.",
            "caution": "",
            "evidence": {"metric": "total_return", "value": 0.1},
            "rule_ids": ["SAFE-POST-001"],
        }
        safe, blocked = _safe_insight(unsafe)

        self.assertIsNotNone(safe)
        self.assertGreaterEqual(len(blocked), 1)
        safe_text = " ".join(str(safe[key]) for key in ("fact", "interpretation", "caution")).lower()
        self.assertFalse(_contains_forbidden(safe_text))

        result = run_pipeline("multi_asset_portfolio.csv")
        insight_text = " ".join(
            " ".join(str(item.get(key, "")) for key in ("fact", "interpretation", "caution"))
            for item in result["insights"]["insights"]
        ).lower()
        report = build_html_report(result).lower()

        self.assertFalse(_contains_forbidden(insight_text))
        self.assertFalse(_contains_forbidden(report))

    def test_applied_rules_visible_with_required_categories(self) -> None:
        result = run_pipeline("multi_asset_portfolio.csv")
        rules = result["applied_rules"]
        prefixes = {record["prefix"] for record in rules}

        self.assertGreaterEqual(len(rules), 5)
        self.assertTrue({"DATA", "SCHEMA", "METRIC", "VIS", "INSIGHT", "SAFE"}.issubset(prefixes))


if __name__ == "__main__":
    unittest.main()
