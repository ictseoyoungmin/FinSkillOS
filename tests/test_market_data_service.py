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


class _FakeYahooResponse:
    def __init__(self, payload: dict, *, status_error: Exception | None = None) -> None:
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self) -> None:
        if self.status_error is not None:
            raise self.status_error

    def json(self) -> dict:
        return self.payload


class _FakeYahooClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, *, params: dict) -> _FakeYahooResponse:
        self.calls.append((url, params))
        return _FakeYahooResponse(self.payload)


def test_yahoo_chart_adapter_normalizes_provider_payload() -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1_777_680_000, 1_777_766_400],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 101.0],
                                "high": [103.0, 104.0],
                                "low": [99.0, 100.0],
                                "close": [102.25, 103.5],
                                "volume": [1000000, 1200000],
                            }
                        ],
                        "adjclose": [{"adjclose": [102.0, 103.25]}],
                    },
                }
            ],
            "error": None,
        }
    }
    client = _FakeYahooClient(payload)
    adapter = YahooChartMarketDataAdapter(client=client)

    bars = adapter.fetch_bars("spy", timeframe="1d")

    assert [bar.ticker for bar in bars] == ["SPY", "SPY"]
    assert bars[0].source == "yahoo"
    assert bars[0].close == Decimal("102.25")
    assert bars[1].volume == Decimal("1200000")
    assert bars[1].adj_close == Decimal("103.25")
    assert client.calls[0][0].endswith("/SPY")
    assert client.calls[0][1]["range"] == "1y"


def test_yahoo_chart_adapter_maps_common_macro_symbols() -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1_777_680_000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [19.0],
                                "high": [20.0],
                                "low": [18.5],
                                "close": [19.5],
                                "volume": [None],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }
    client = _FakeYahooClient(payload)
    adapter = YahooChartMarketDataAdapter(client=client)

    bars = adapter.fetch_bars("VIX")

    assert bars[0].ticker == "VIX"
    assert client.calls[0][0].endswith("/^VIX")


def test_yahoo_chart_adapter_raises_fetch_error_for_empty_payload() -> None:
    adapter = YahooChartMarketDataAdapter(
        client=_FakeYahooClient({"chart": {"result": [], "error": None}})
    )

    try:
        adapter.fetch_bars("SPY")
    except MarketDataFetchError as exc:
        assert "no result" in str(exc)
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
