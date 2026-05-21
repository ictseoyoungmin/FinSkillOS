"""Shared constants + helpers for the fixture builders."""

from __future__ import annotations

from decimal import Decimal

# Stable timestamp so visual baselines stay deterministic across runs.
FIXTURE_TIMESTAMP = "2026-05-20T12:00:00+09:00"

# Bars shown by the chart panels — same calendar so dashboards line up.
# Newest first, oldest last; consumers reverse if they need ascending.
FIXTURE_BAR_DATES = (
    "2026-04-20T00:00:00+00:00",
    "2026-04-21T00:00:00+00:00",
    "2026-04-22T00:00:00+00:00",
    "2026-04-23T00:00:00+00:00",
    "2026-04-24T00:00:00+00:00",
    "2026-04-27T00:00:00+00:00",
    "2026-04-28T00:00:00+00:00",
    "2026-04-29T00:00:00+00:00",
    "2026-04-30T00:00:00+00:00",
    "2026-05-01T00:00:00+00:00",
    "2026-05-04T00:00:00+00:00",
    "2026-05-05T00:00:00+00:00",
    "2026-05-06T00:00:00+00:00",
    "2026-05-07T00:00:00+00:00",
    "2026-05-08T00:00:00+00:00",
    "2026-05-11T00:00:00+00:00",
    "2026-05-12T00:00:00+00:00",
    "2026-05-13T00:00:00+00:00",
    "2026-05-14T00:00:00+00:00",
    "2026-05-15T00:00:00+00:00",
    "2026-05-18T00:00:00+00:00",
    "2026-05-19T00:00:00+00:00",
)


def D(value: str) -> Decimal:
    """Short Decimal constructor — fixture files use it extensively."""

    return Decimal(value)
