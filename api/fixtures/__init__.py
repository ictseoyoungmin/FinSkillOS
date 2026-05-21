"""Deterministic API fixtures — Slice 13.6 + 13.7.

Each FastAPI route has a sibling builder in this package so the React
shell can render a stable v4.1 cockpit visual baseline without
depending on live DB / regime / news data. The fixture path is also
the ground truth used by Playwright visual tests.

Importable shortcuts mirror the layout used in Slice 13.6:

* ``control_room_fixture()`` + ``CONTROL_ROOM_FIXTURE_TIMESTAMP``
* ``market_kernel_fixture(ticker)`` (Slice 13.7)
* ``analysis_workspace_fixture()`` (Slice 13.7)
* ``symbol_lab_fixture(ticker)`` (Slice 13.7)
"""

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.fixtures.analysis_workspace import analysis_workspace_fixture
from api.fixtures.control_room import (
    CONTROL_ROOM_FIXTURE_TIMESTAMP,
    control_room_fixture,
)
from api.fixtures.market_kernel import (
    MARKET_KERNEL_DEFAULT_TICKER,
    SUPPORTED_FOCUS_TICKERS,
    market_kernel_fixture,
)
from api.fixtures.symbol_lab import (
    SYMBOL_LAB_DEFAULT_TICKER,
    symbol_lab_fixture,
)

__all__ = [
    "CONTROL_ROOM_FIXTURE_TIMESTAMP",
    "FIXTURE_TIMESTAMP",
    "MARKET_KERNEL_DEFAULT_TICKER",
    "SUPPORTED_FOCUS_TICKERS",
    "SYMBOL_LAB_DEFAULT_TICKER",
    "analysis_workspace_fixture",
    "control_room_fixture",
    "market_kernel_fixture",
    "symbol_lab_fixture",
]
