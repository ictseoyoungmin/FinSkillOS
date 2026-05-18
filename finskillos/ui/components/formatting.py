"""Pure formatting helpers shared across Slice-07 UI components.

Kept Streamlit-free so the test suite can import them directly and
verify rendering against fixed strings.
"""

from __future__ import annotations

from decimal import Decimal

from finskillos.guards.base import (
    RISK_GREEN,
    RISK_ORANGE,
    RISK_RED,
    RISK_UNKNOWN,
    RISK_YELLOW,
    STATUS_BLOCKED,
    STATUS_FAIL,
    STATUS_INFO,
    STATUS_PASS,
    STATUS_WARN,
)

_RISK_COLOR = {
    RISK_GREEN: "#00cc66",
    RISK_YELLOW: "#ffb800",
    RISK_ORANGE: "#ff9100",
    RISK_RED: "#ff3b5c",
    RISK_UNKNOWN: "#6090b8",
}

_STATUS_LABEL_KO = {
    STATUS_PASS: "정상",
    STATUS_INFO: "정보",
    STATUS_WARN: "주의",
    STATUS_FAIL: "경고",
    STATUS_BLOCKED: "보호 모드",
}


def format_krw(value: Decimal | int | float | None) -> str:
    if value is None:
        return "—"
    return f"{Decimal(value):,.0f} KRW"


def format_pct(value: Decimal | int | float | None, *, places: int = 1) -> str:
    if value is None:
        return "—"
    return f"{Decimal(value):.{places}f}%"


def format_ratio(value: Decimal | int | float | None, *, places: int = 1) -> str:
    """0–1 ratio rendered as a percent (e.g. 0.35 → 35.0%)."""

    if value is None:
        return "—"
    return f"{(Decimal(value) * Decimal('100')):.{places}f}%"


def risk_color(level: str) -> str:
    return _RISK_COLOR.get(level, _RISK_COLOR[RISK_UNKNOWN])


def status_label(status: str) -> str:
    return _STATUS_LABEL_KO.get(status, status)


def status_emoji(status: str) -> str:
    """A compact symbol the Streamlit cards prepend to a status badge."""

    return {
        STATUS_PASS: "✓",
        STATUS_INFO: "•",
        STATUS_WARN: "▲",
        STATUS_FAIL: "✕",
        STATUS_BLOCKED: "■",
    }.get(status, "•")
