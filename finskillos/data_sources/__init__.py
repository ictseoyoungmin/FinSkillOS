"""Provider-agnostic data source layer.

Exports the canonical DTO types and the market-data adapter
abstractions used by Slice 04. Concrete providers (yfinance,
Alpha Vantage, Polygon, ...) plug in via the `BaseMarketDataAdapter`
interface; tests rely on the deterministic `MockMarketDataAdapter` so
nothing in this slice depends on a live internet connection.
"""

from finskillos.data_sources.adapters.yfinance_adapter import YahooChartMarketDataAdapter
from finskillos.data_sources.dto import (
    DEFAULT_TIMEFRAME,
    DEFAULT_US_TICKER_UNIVERSE,
    IndicatorSnapshotDTO,
    MarketBarDTO,
)
from finskillos.data_sources.market_adapter import (
    BaseMarketDataAdapter,
    CsvMarketDataAdapter,
    MarketDataFetchError,
    MockMarketDataAdapter,
)

__all__ = [
    "BaseMarketDataAdapter",
    "CsvMarketDataAdapter",
    "DEFAULT_TIMEFRAME",
    "DEFAULT_US_TICKER_UNIVERSE",
    "IndicatorSnapshotDTO",
    "MarketBarDTO",
    "MarketDataFetchError",
    "MockMarketDataAdapter",
    "YahooChartMarketDataAdapter",
]
