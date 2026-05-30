"""Shared live-state helpers + copy (Slice 80 contract; Slice 92).

The per-tab live-error builders (risk_firewall / mission_control /
news_intelligence / trade_memory) repeat the same exception-detail rule and the
same two narrative sentences. Centralising them keeps the state language
(``docs/v2_1/13_State_Vocabulary_And_Data_Source_Contract.md``) from drifting
between routes. The route-specific phrasing (e.g. "Live risk evaluation failed")
stays in each route.
"""

from __future__ import annotations


def exc_detail(exc: Exception) -> str:
    """The exception class name only — never the message or stack trace."""
    return type(exc).__name__


# Shared narrative for the live-error state (DB reachable, the read raised).
LIVE_ERROR_DRIVER_NOTE = (
    "An error is surfaced instead of falling back to fixture data."
)
LIVE_ERROR_WHY_IT_MATTERS = (
    "Errors are surfaced explicitly rather than masked with fixture data."
)


__all__ = [
    "LIVE_ERROR_DRIVER_NOTE",
    "LIVE_ERROR_WHY_IT_MATTERS",
    "exc_detail",
]
