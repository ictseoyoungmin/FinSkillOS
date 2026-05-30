"""Slice 91 — shared api.timeutil contract."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from api.timeutil import iso, to_utc

_KST = timezone(timedelta(hours=9))


def test_to_utc_assumes_naive_is_utc() -> None:
    naive = datetime(2026, 5, 30, 12, 0, 0)
    assert to_utc(naive) == datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)


def test_to_utc_converts_aware_to_utc() -> None:
    kst = datetime(2026, 5, 30, 21, 0, 0, tzinfo=_KST)
    assert to_utc(kst) == datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)


def test_iso_normalises_naive_datetime_to_utc() -> None:
    assert iso(datetime(2026, 5, 30, 12, 0, 0)) == "2026-05-30T12:00:00+00:00"


def test_iso_converts_aware_datetime_to_utc() -> None:
    assert iso(datetime(2026, 5, 30, 21, 0, 0, tzinfo=_KST)) == (
        "2026-05-30T12:00:00+00:00"
    )


def test_iso_date_matches_isoformat() -> None:
    d = date(2026, 5, 30)
    assert iso(d) == d.isoformat() == "2026-05-30"


def test_iso_non_datetime_falls_back_to_str() -> None:
    assert iso(None) == "None"
    assert iso("already-a-string") == "already-a-string"
