"""Deterministic API fixtures — Slice 13.6 + 13.7 + 13.8 + 13.9.

Each FastAPI route has a sibling builder in this package so the React
shell can render a stable v4.1 cockpit visual baseline without
depending on live DB / regime / news data. The fixture path is also
the ground truth used by Playwright visual tests.

Importable shortcuts mirror the layout used in earlier slices:

* ``control_room_fixture()`` + ``CONTROL_ROOM_FIXTURE_TIMESTAMP``
* ``market_kernel_fixture(ticker)`` (Slice 13.7)
* ``analysis_workspace_fixture()`` (Slice 13.7)
* ``symbol_lab_fixture(ticker)`` (Slice 13.7)
* ``risk_firewall_fixture()`` (Slice 13.8)
* ``mission_control_fixture()`` (Slice 13.8)
* ``system_ops_fixture()`` (Slice 13.8)
* ``news_intelligence_fixture()`` (Slice 13.9)
* ``event_radar_fixture()`` (Slice 13.9)
* ``trade_memory_fixture()`` (Slice 13.9)
"""

from api.fixtures._common import FIXTURE_TIMESTAMP
from api.fixtures.analysis_workspace import analysis_workspace_fixture
from api.fixtures.control_room import (
    CONTROL_ROOM_FIXTURE_TIMESTAMP,
    control_room_fixture,
)
from api.fixtures.event_radar import event_radar_fixture
from api.fixtures.market_kernel import (
    MARKET_KERNEL_DEFAULT_TICKER,
    SUPPORTED_FOCUS_TICKERS,
    market_kernel_fixture,
)
from api.fixtures.mission_control import mission_control_fixture
from api.fixtures.news_intelligence import news_intelligence_fixture
from api.fixtures.risk_firewall import risk_firewall_fixture
from api.fixtures.symbol_lab import (
    SYMBOL_LAB_DEFAULT_TICKER,
    symbol_lab_fixture,
)
from api.fixtures.system_ops import system_ops_fixture
from api.fixtures.trade_memory import trade_memory_fixture

__all__ = [
    "CONTROL_ROOM_FIXTURE_TIMESTAMP",
    "FIXTURE_TIMESTAMP",
    "MARKET_KERNEL_DEFAULT_TICKER",
    "SUPPORTED_FOCUS_TICKERS",
    "SYMBOL_LAB_DEFAULT_TICKER",
    "analysis_workspace_fixture",
    "control_room_fixture",
    "event_radar_fixture",
    "market_kernel_fixture",
    "mission_control_fixture",
    "news_intelligence_fixture",
    "risk_firewall_fixture",
    "symbol_lab_fixture",
    "system_ops_fixture",
    "trade_memory_fixture",
]
