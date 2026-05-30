"""Shared time helpers for the API routes (Slice 91).

Several routes carried byte-identical ``_as_utc`` and near-identical ``_iso``
helpers. They are consolidated here so the timestamp contract is defined once.
"""

from __future__ import annotations

from datetime import datetime, timezone

UTC = timezone.utc


def to_utc(value: datetime) -> datetime:
    """Return ``value`` as a UTC-aware datetime (naive inputs are assumed UTC)."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def iso(value: object) -> str:
    """ISO-8601 string for a datetime, normalised to UTC.

    Naive datetimes are assumed UTC; aware datetimes are converted to UTC.
    Non-datetime values (``date``, ``None``, …) fall back to ``str(value)`` —
    for ``date`` this matches ``date.isoformat()``.
    """
    if isinstance(value, datetime):
        return to_utc(value).isoformat()
    return str(value)


__all__ = ["UTC", "iso", "to_utc"]
