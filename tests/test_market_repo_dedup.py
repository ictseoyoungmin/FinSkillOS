"""Slice 101 — MarketRepository same-day source dedup.

A mock seed bar (00:00 UTC) and a real vendor bar (04:00 UTC) can land on
the same calendar day for a daily-or-coarser timeframe, since the unique key
is ``(ticker, timeframe, bar_time)`` and the two differ by time-of-day. The
chart must render one point per day (preferring the real source) instead of
sawtoothing between the two series. Intraday timeframes keep every bar.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.repositories import MarketRepository

UTC = timezone.utc


def _bar(ticker: str, timeframe: str, bar_time: datetime, close: str, source: str):
    return MarketBarDTO(
        ticker=ticker,
        timeframe=timeframe,
        bar_time=bar_time,
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        adj_close=Decimal(close),
        volume=Decimal("1000"),
        source=source,
    )


def test_daily_same_day_dedup_prefers_real_source(db_session) -> None:
    repo = MarketRepository(db_session)
    # Same calendar day, two sources at different times.
    repo.upsert_bar(
        _bar("NVDA", "1d", datetime(2026, 5, 29, 0, 0, tzinfo=UTC), "229.20", "mock")
    )
    repo.upsert_bar(
        _bar(
            "NVDA", "1d", datetime(2026, 5, 29, 4, 0, tzinfo=UTC), "211.14", "yfinance"
        )
    )
    # A clean prior day with only the real source.
    repo.upsert_bar(
        _bar(
            "NVDA", "1d", datetime(2026, 5, 28, 4, 0, tzinfo=UTC), "210.00", "yfinance"
        )
    )
    db_session.flush()

    bars = repo.list_bars("NVDA", "1d")
    assert len(bars) == 2
    # The 2026-05-29 collision collapses to the yfinance close, not the mock one.
    last = bars[-1]
    assert last.bar_time.date().isoformat() == "2026-05-29"
    assert last.source == "yfinance"
    assert last.close == Decimal("211.14")


def test_mock_only_day_is_retained(db_session) -> None:
    repo = MarketRepository(db_session)
    repo.upsert_bar(
        _bar(
            "NVDA", "1d", datetime(2026, 5, 29, 4, 0, tzinfo=UTC), "211.14", "yfinance"
        )
    )
    # A day with no real bar keeps the mock one (no coverage loss).
    repo.upsert_bar(
        _bar("NVDA", "1d", datetime(2026, 5, 30, 0, 0, tzinfo=UTC), "251.14", "mock")
    )
    db_session.flush()

    bars = repo.list_bars("NVDA", "1d")
    assert len(bars) == 2
    assert bars[-1].source == "mock"


def test_intraday_keeps_multiple_bars_per_day(db_session) -> None:
    repo = MarketRepository(db_session)
    for hour in (13, 14, 15):
        repo.upsert_bar(
            _bar(
                "NVDA",
                "1h",
                datetime(2026, 5, 29, hour, 0, tzinfo=UTC),
                f"21{hour}.0",
                "yfinance",
            )
        )
    db_session.flush()

    bars = repo.list_bars("NVDA", "1h")
    # Intraday: every bar in the same day is legitimate, none collapsed.
    assert len(bars) == 3
