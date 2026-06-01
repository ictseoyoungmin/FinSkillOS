"""Slice 04 — MarketDataService + adapter tests.

Covers DATA-AC-001 / DATA-AC-002 / FAIL-AC-001 plus the structural
guarantees from .devmd/04: incremental upsert by (ticker, timeframe,
bar_time), per-ticker failure isolation, CSV import path, and the
default US-market focus universe.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from finskillos.data_sources import (
    DEFAULT_US_TICKER_UNIVERSE,
    CsvMarketDataAdapter,
    MarketDataFetchError,
    MockMarketDataAdapter,
    YahooChartMarketDataAdapter,
)
from finskillos.data_sources.dto import MarketBarDTO
from finskillos.db.repositories import MarketRepository
from finskillos.services.market_data_service import MarketDataService

UTC = timezone.utc
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "market_bars"


def test_mock_adapter_is_deterministic_per_ticker() -> None:
    adapter = MockMarketDataAdapter(default_bars=30)
    first = adapter.fetch_bars("SPY", timeframe="1d")
    second = adapter.fetch_bars("SPY", timeframe="1d")
    assert len(first) == 30 == len(second)
    assert [b.close for b in first] == [b.close for b in second]
    # Different tickers must diverge so the same seed cannot collide.
    tsla = adapter.fetch_bars("TSLA", timeframe="1d")
    assert [b.close for b in tsla] != [b.close for b in first]


def test_mock_adapter_respects_failing_ticker_set() -> None:
    adapter = MockMarketDataAdapter(failing_tickers={"VIX"})
    try:
        adapter.fetch_bars("VIX")
    except MarketDataFetchError:
        pass
    else:  # pragma: no cover - assertion failure
        raise AssertionError("expected MarketDataFetchError for VIX")
    # Other tickers in the same pass still resolve.
    assert adapter.fetch_bars("SPY", timeframe="1d")


def test_csv_adapter_loads_sample_fixture() -> None:
    adapter = CsvMarketDataAdapter(FIXTURES / "sample_daily_bars.csv")
    bars = adapter.fetch_bars("SPY", timeframe="1d")
    assert [b.ticker for b in bars] == ["SPY"] * 10
    assert bars[0].bar_time == datetime(2026, 5, 1, tzinfo=UTC)
    assert bars[-1].close == Decimal("514.0")


def test_csv_adapter_raises_for_unknown_ticker() -> None:
    adapter = CsvMarketDataAdapter(FIXTURES / "sample_daily_bars.csv")
    try:
        adapter.fetch_bars("UNKNOWN", timeframe="1d")
    except MarketDataFetchError:
        return
    raise AssertionError("expected MarketDataFetchError for unknown ticker")


class _FakeYahooClient:
    def __init__(self, rows: list[tuple[datetime, dict]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, dict]] = []

    def Ticker(self, symbol: str):  # noqa: N802 - mirrors yfinance API
        client = self

        class _Ticker:
            def history(self, **kwargs):  # noqa: ANN001
                client.calls.append((symbol, kwargs))
                return _FakeHistory(client.rows)

        return _Ticker()


class _FakeHistory:
    def __init__(self, rows: list[tuple[datetime, dict]]) -> None:
        self.rows = rows
        self.empty = not rows

    def iterrows(self):
        return iter(self.rows)


def test_yahoo_chart_adapter_normalizes_provider_payload() -> None:
    client = _FakeYahooClient(
        [
            (
                datetime(2026, 5, 1, tzinfo=UTC),
                {
                    "Open": 100.0,
                    "High": 103.0,
                    "Low": 99.0,
                    "Close": 102.25,
                    "Volume": 1000000,
                    "Adj Close": 102.0,
                },
            ),
            (
                datetime(2026, 5, 2, tzinfo=UTC),
                {
                    "Open": 101.0,
                    "High": 104.0,
                    "Low": 100.0,
                    "Close": 103.5,
                    "Volume": 1200000,
                    "Adj Close": 103.25,
                },
            ),
        ]
    )
    adapter = YahooChartMarketDataAdapter(client=client)

    bars = adapter.fetch_bars("spy", timeframe="1d")

    assert [bar.ticker for bar in bars] == ["SPY", "SPY"]
    assert bars[0].source == "yfinance"
    assert bars[0].close == Decimal("102.25")
    assert bars[1].volume == Decimal("1200000")
    assert bars[1].adj_close == Decimal("103.25")
    assert client.calls[0][0] == "SPY"
    assert client.calls[0][1]["period"] == "1y"
    assert client.calls[0][1]["interval"] == "1d"


def test_yahoo_chart_adapter_supports_symbol_lab_timeframes() -> None:
    for timeframe, interval, canonical, period in (
        ("5m", "5m", "5m", "5d"),
        ("15m", "15m", "15m", "1mo"),
        ("1h", "1h", "1h", "60d"),
        ("1d", "1d", "1d", "1y"),
        ("1w", "1wk", "1wk", "5y"),
        ("1mon", "1mo", "1mo", "10y"),
        ("1y", "1mo", "1y", "10y"),
    ):
        client = _FakeYahooClient(
            [
                (
                    datetime(2026, 5, 1, tzinfo=UTC),
                    {
                        "Open": 100.0,
                        "High": 103.0,
                        "Low": 99.0,
                        "Close": 102.25,
                        "Volume": 1000000,
                    },
                ),
            ]
        )
        adapter = YahooChartMarketDataAdapter(client=client)

        bars = adapter.fetch_bars("TSLA", timeframe=timeframe)

        assert client.calls[0][1]["interval"] == interval
        assert client.calls[0][1]["period"] == period
        assert bars[0].timeframe == canonical


def test_yahoo_chart_adapter_aggregates_monthly_rows_to_annual_bars() -> None:
    client = _FakeYahooClient(
        [
            (
                datetime(2025, 12, 1, tzinfo=UTC),
                {
                    "Open": 90.0,
                    "High": 110.0,
                    "Low": 85.0,
                    "Close": 100.0,
                    "Volume": 1000,
                    "Adj Close": 99.0,
                },
            ),
            (
                datetime(2026, 1, 1, tzinfo=UTC),
                {
                    "Open": 100.0,
                    "High": 125.0,
                    "Low": 95.0,
                    "Close": 120.0,
                    "Volume": 2000,
                    "Adj Close": 119.0,
                },
            ),
            (
                datetime(2026, 2, 1, tzinfo=UTC),
                {
                    "Open": 120.0,
                    "High": 130.0,
                    "Low": 90.0,
                    "Close": 115.0,
                    "Volume": 3000,
                    "Adj Close": 114.0,
                },
            ),
        ]
    )
    adapter = YahooChartMarketDataAdapter(client=client)

    bars = adapter.fetch_bars("TSLA", timeframe="1y")

    assert client.calls[0][1]["interval"] == "1mo"
    assert client.calls[0][1]["period"] == "10y"
    assert [bar.bar_time.year for bar in bars] == [2025, 2026]
    assert [bar.timeframe for bar in bars] == ["1y", "1y"]
    assert bars[0].open == Decimal("90.0")
    assert bars[0].high == Decimal("110.0")
    assert bars[0].low == Decimal("85.0")
    assert bars[0].close == Decimal("100.0")
    assert bars[0].volume == Decimal("1000")
    assert bars[1].open == Decimal("100.0")
    assert bars[1].high == Decimal("130.0")
    assert bars[1].low == Decimal("90.0")
    assert bars[1].close == Decimal("115.0")
    assert bars[1].volume == Decimal("5000")
    assert bars[1].adj_close == Decimal("114.0")


def test_refresh_bars_revalidates_when_latest_source_changes(
    db_session: Session,
) -> None:
    mock_service = MarketDataService(
        db_session,
        adapter=MockMarketDataAdapter(default_bars=3),
        universe=["SPY"],
    )
    mock_service.refresh_bars(["SPY"])
    assert MarketRepository(db_session).latest_bar("SPY", "1d").source == "mock"

    yahoo_client = _FakeYahooClient(
        [
            (
                datetime(2026, 5, 26, tzinfo=UTC),
                {
                    "Open": 700.0,
                    "High": 731.0,
                    "Low": 699.0,
                    "Close": 730.28,
                    "Volume": 1000000,
                },
            ),
        ]
    )
    yahoo_service = MarketDataService(
        db_session,
        adapter=YahooChartMarketDataAdapter(client=yahoo_client),
        universe=["SPY"],
    )

    report = yahoo_service.refresh_bars(["SPY"])

    assert yahoo_client.calls[0][1]["period"] == "1y"
    assert yahoo_client.calls[0][1].get("start") is None
    assert report.total_bars_written == 1
    latest = MarketRepository(db_session).latest_bar("SPY", "1d")
    assert latest.source == "yfinance"
    assert latest.close == Decimal("730.28")


def test_refresh_bars_force_full_replaces_existing_timeframe(
    db_session: Session,
) -> None:
    initial = MarketBarDTO(
        ticker="SPY",
        timeframe="1mo",
        bar_time=datetime(2026, 5, 1, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1000"),
        source="mock",
    )
    MarketDataService(db_session).import_bars([initial])
    client = _FakeYahooClient(
        [
            (
                datetime(2026, 4, 1, tzinfo=UTC),
                {
                    "Open": 700.0,
                    "High": 731.0,
                    "Low": 699.0,
                    "Close": 730.28,
                    "Volume": 1000000,
                },
            )
        ]
    )
    service = MarketDataService(
        db_session,
        adapter=YahooChartMarketDataAdapter(client=client),
        universe=["SPY"],
    )

    report = service.refresh_bars(["SPY"], timeframe="1mo", force_full=True)

    rows = MarketRepository(db_session).list_bars("SPY", "1mo")
    assert report.total_bars_written == 1
    assert len(rows) == 1
    assert rows[0].source == "yfinance"
    assert rows[0].close == Decimal("730.28")


def test_yahoo_chart_adapter_maps_common_macro_symbols() -> None:
    client = _FakeYahooClient(
        [
            (
                datetime(2026, 5, 1, tzinfo=UTC),
                {
                    "Open": 19.0,
                    "High": 20.0,
                    "Low": 18.5,
                    "Close": 19.5,
                    "Volume": None,
                },
            )
        ]
    )
    adapter = YahooChartMarketDataAdapter(client=client)

    bars = adapter.fetch_bars("VIX")

    assert bars[0].ticker == "VIX"
    assert client.calls[0][0] == "^VIX"


def test_yahoo_chart_adapter_raises_fetch_error_for_empty_payload() -> None:
    adapter = YahooChartMarketDataAdapter(client=_FakeYahooClient([]))

    try:
        adapter.fetch_bars("SPY")
    except MarketDataFetchError as exc:
        assert "no history rows" in str(exc)
    else:  # pragma: no cover - assertion failure
        raise AssertionError("expected MarketDataFetchError for empty Yahoo payload")


def test_refresh_bars_writes_initial_history(db_session: Session) -> None:
    adapter = MockMarketDataAdapter(default_bars=10)
    service = MarketDataService(db_session, adapter=adapter, universe=["SPY"])
    report = service.refresh_bars(["SPY"])

    assert report.total_bars_written == 10
    assert report.failed == ()
    rows = MarketRepository(db_session).list_bars("SPY", "1d")
    assert len(rows) == 10
    assert rows[0].source == "mock"


def test_refresh_bars_is_incremental(db_session: Session) -> None:
    """DATA-AC-002: re-running refresh only appends new bars."""

    # Round 1: import bars 2026-05-01 .. 2026-05-05.
    initial = CsvMarketDataAdapter(FIXTURES / "sample_daily_bars.csv")
    service = MarketDataService(db_session, adapter=initial)
    # Limit the adapter to early window by overriding fetch via a wrapper.

    class _WindowedAdapter:
        source_name = "csv"

        def fetch_bars(
            self, ticker, *, timeframe="1d", start=None, end=None
        ):  # noqa: ANN001
            bars = initial.fetch_bars(ticker, timeframe=timeframe)
            cutoff = datetime(2026, 5, 5, tzinfo=UTC)
            filtered = [b for b in bars if b.bar_time <= cutoff]
            if start is not None:
                filtered = [b for b in filtered if b.bar_time > start]
            return filtered

    service.adapter = _WindowedAdapter()  # type: ignore[assignment]
    first_report = service.refresh_bars(["SPY"])
    assert first_report.total_bars_written == 5

    # Round 2: full CSV available — only the bars *after* 2026-05-05 should be
    # written; the existing five rows must not duplicate.
    service.adapter = initial
    second_report = service.refresh_bars(["SPY"])
    assert second_report.total_bars_written == 5  # 2026-05-06 .. 2026-05-10

    rows = MarketRepository(db_session).list_bars("SPY", "1d")
    assert len(rows) == 10
    # SQLite drops tzinfo on read; compare on the calendar day instead.
    assert {r.bar_time.date() for r in rows} == {
        datetime(2026, 5, day).date() for day in range(1, 11)
    }


def test_refresh_isolates_per_ticker_failures(db_session: Session) -> None:
    """FAIL-AC-001: one bad ticker must not break the whole refresh."""

    adapter = MockMarketDataAdapter(default_bars=12, failing_tickers={"VIX"})
    service = MarketDataService(
        db_session, adapter=adapter, universe=["SPY", "VIX", "TSLA"]
    )
    report = service.refresh_bars()

    failed_tickers = {r.ticker for r in report.failed}
    assert failed_tickers == {"VIX"}
    ok_tickers = {r.ticker for r in report.succeeded}
    assert {"SPY", "TSLA"}.issubset(ok_tickers)
    # Surviving tickers persisted their bars.
    assert MarketRepository(db_session).count_for("SPY", "1d") == 12
    assert MarketRepository(db_session).count_for("TSLA", "1d") == 12


def test_get_latest_price_returns_close_of_latest_bar(db_session: Session) -> None:
    adapter = CsvMarketDataAdapter(FIXTURES / "sample_daily_bars.csv")
    service = MarketDataService(db_session, adapter=adapter)
    service.refresh_bars(["TSLA"])
    assert service.get_latest_price("TSLA") == Decimal("197.5")


def test_default_universe_is_us_market_focused() -> None:
    universe = set(DEFAULT_US_TICKER_UNIVERSE)
    required = {"SPY", "QQQ", "NVDA", "TSLA", "AAPL", "MSFT", "AMZN"}
    assert required.issubset(universe)


def test_default_universe_covers_analysis_index_universe() -> None:
    """Slice 116 — a single refresh must populate every Analysis Workspace row,
    so the refresh universe is a superset of the Index Lab universe (no
    permanently-MISSING sector ETFs)."""
    from finskillos.ui.view_models.index_lab_vm import DEFAULT_INDEX_UNIVERSE

    refresh = set(DEFAULT_US_TICKER_UNIVERSE)
    index_universe = {entry.ticker for entry in DEFAULT_INDEX_UNIVERSE}
    missing = index_universe - refresh
    assert not missing, f"refresh universe omits Analysis tickers: {sorted(missing)}"


def test_import_bars_bypasses_adapter(db_session: Session) -> None:
    from finskillos.data_sources.dto import MarketBarDTO

    service = MarketDataService(db_session)
    bars = [
        MarketBarDTO(
            ticker="PLTR",
            timeframe="1d",
            bar_time=datetime(2026, 5, day, tzinfo=UTC),
            open=Decimal("20"),
            high=Decimal("22"),
            low=Decimal("19"),
            close=Decimal("21"),
            volume=Decimal("3000000"),
            source="manual",
        )
        for day in range(10, 15)
    ]
    written = service.import_bars(bars)
    assert written == 5
    # Re-importing the same set must upsert (idempotent), not duplicate.
    written_again = service.import_bars(bars)
    assert written_again == 5
    assert MarketRepository(db_session).count_for("PLTR", "1d") == 5
