"""Shared coverage vocabulary for the Market Kernel and Symbol Lab tabs.

Slice 74 made the two tabs share the ``coverageLevel`` /
``evidenceCoveragePercent`` / ``missingSummary`` field contract; Slice 77 graded
Symbol Lab's sparse/partial copy quantitatively. Slice 83 promotes that graded
copy into this single helper so both tabs read identically — the only per-tab
difference is the ``domain`` label in the COMPLETE summary.
"""

from __future__ import annotations

# Minimum stored-bar window for a stable indicator snapshot. Below this count a
# tab reports SPARSE coverage and grades how many bars remain.
INDICATOR_WARMUP_BARS = 20


def coverage_level(*, bar_count: int, indicator_status: str) -> str:
    if bar_count <= 0:
        return "EMPTY"
    if bar_count < INDICATOR_WARMUP_BARS:
        return "SPARSE"
    if indicator_status != "AVAILABLE":
        return "PARTIAL"
    return "COMPLETE"


def evidence_coverage_percent(*, bar_count: int, indicator_status: str) -> int:
    if bar_count <= 0:
        return 0
    bar_score = min(bar_count / INDICATOR_WARMUP_BARS, 1.0) * 70
    indicator_score = {
        "AVAILABLE": 30,
        "PARTIAL": 15,
        "MISSING": 0,
    }.get(indicator_status, 0)
    return round(bar_score + indicator_score)


def missing_summary(
    *,
    domain: str,
    ticker: str,
    bar_count: int,
    coverage_level: str,
    indicator_status: str,
) -> str:
    if coverage_level == "COMPLETE":
        return f"No missing {domain} evidence."
    if coverage_level == "EMPTY":
        return f"{ticker} needs stored bars and indicators."
    if coverage_level == "SPARSE":
        remaining = max(INDICATOR_WARMUP_BARS - bar_count, 0)
        return (
            f"{ticker} has {bar_count} of {INDICATOR_WARMUP_BARS} stored bars; "
            f"{remaining} more complete the indicator window."
        )
    if indicator_status != "AVAILABLE":
        return (
            f"{ticker} has {bar_count} stored bars but the latest indicator "
            "snapshot is incomplete."
        )
    return f"{ticker} evidence is partial."


__all__ = [
    "INDICATOR_WARMUP_BARS",
    "coverage_level",
    "evidence_coverage_percent",
    "missing_summary",
]
