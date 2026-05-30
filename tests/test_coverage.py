"""Slice 83 — shared Market Kernel / Symbol Lab coverage vocabulary."""

from __future__ import annotations

from api.coverage import (
    INDICATOR_WARMUP_BARS,
    coverage_level,
    evidence_coverage_percent,
    missing_summary,
)


def test_coverage_level_thresholds() -> None:
    assert coverage_level(bar_count=0, indicator_status="MISSING") == "EMPTY"
    assert coverage_level(bar_count=1, indicator_status="AVAILABLE") == "SPARSE"
    assert (
        coverage_level(
            bar_count=INDICATOR_WARMUP_BARS, indicator_status="PARTIAL"
        )
        == "PARTIAL"
    )
    assert (
        coverage_level(
            bar_count=INDICATOR_WARMUP_BARS, indicator_status="AVAILABLE"
        )
        == "COMPLETE"
    )


def test_evidence_coverage_percent_matches_legacy_formula() -> None:
    assert evidence_coverage_percent(bar_count=0, indicator_status="MISSING") == 0
    # 1/20 * 70 = 3.5, + 30 (AVAILABLE) = 33.5 -> 34 (banker's rounding).
    assert evidence_coverage_percent(bar_count=1, indicator_status="AVAILABLE") == 34
    assert (
        evidence_coverage_percent(bar_count=40, indicator_status="AVAILABLE") == 100
    )


def test_missing_summary_complete_is_domain_specific() -> None:
    assert (
        missing_summary(
            domain="market-kernel",
            ticker="SPY",
            bar_count=40,
            coverage_level="COMPLETE",
            indicator_status="AVAILABLE",
        )
        == "No missing market-kernel evidence."
    )
    assert (
        missing_summary(
            domain="symbol-lab",
            ticker="NVDA",
            bar_count=40,
            coverage_level="COMPLETE",
            indicator_status="AVAILABLE",
        )
        == "No missing symbol-lab evidence."
    )


def test_missing_summary_sparse_is_graded_and_domain_independent() -> None:
    # SPARSE / PARTIAL / EMPTY copy is identical across tabs — only COMPLETE
    # carries the domain label.
    for domain in ("market-kernel", "symbol-lab"):
        assert missing_summary(
            domain=domain,
            ticker="SPY",
            bar_count=1,
            coverage_level="SPARSE",
            indicator_status="AVAILABLE",
        ) == (
            "SPY has 1 of 20 stored bars; 19 more complete the indicator window."
        )


def test_missing_summary_partial_reports_indicator_gap() -> None:
    assert missing_summary(
        domain="market-kernel",
        ticker="SPY",
        bar_count=44,
        coverage_level="PARTIAL",
        indicator_status="PARTIAL",
    ) == (
        "SPY has 44 stored bars but the latest indicator snapshot is incomplete."
    )


def test_missing_summary_empty_needs_bars_and_indicators() -> None:
    assert missing_summary(
        domain="symbol-lab",
        ticker="ZZZZZ",
        bar_count=0,
        coverage_level="EMPTY",
        indicator_status="MISSING",
    ) == "ZZZZZ needs stored bars and indicators."
