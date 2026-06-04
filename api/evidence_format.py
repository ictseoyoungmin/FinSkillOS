"""Shared evidence-dict humaniser for the Phase 4 interpretation engine.

Guards (Slice 163) and the regime engine (Slice 164) both attach a raw
``evidence`` dict — the numbers behind a decision — to their results. These
helpers turn that dict into readable ``(label, value)`` rows so each tab can
render a "why?" drilldown without re-running the engine. Descriptive only.
"""

from __future__ import annotations

from decimal import Decimal

__all__ = ["humanize_key", "format_evidence_value", "evidence_rows"]


def humanize_key(key: str) -> str:
    """``over_limit_tickers`` -> ``Over limit tickers``."""
    return key.replace("_", " ").strip().capitalize() or key


def format_evidence_value(value: object) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        # JSON round-trips Decimals to floats; normalise integral ones (58.0 -> 58).
        return _format_decimal(Decimal(str(value)))
    if isinstance(value, dict):
        return "; ".join(
            f"{k}: {format_evidence_value(v)}" for k, v in value.items()
        )
    if isinstance(value, (list, tuple)):
        return ", ".join(format_evidence_value(v) for v in value)
    return str(value)


def evidence_rows(evidence: dict[str, object]) -> list[tuple[str, str]]:
    """Readable ``(label, value)`` rows, skipping empty values."""
    return [
        (humanize_key(key), format_evidence_value(value))
        for key, value in evidence.items()
        if value is not None and value != [] and value != {}
    ]


def _format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return f"{value:,.0f}"
    return f"{value:,.2f}"
