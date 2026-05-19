"""Slice-07+ UI view models — DB-backed, Streamlit-free read models.

These dataclasses wrap the existing service / repository layer so the
Streamlit pages stay thin and the orchestration logic can be tested
without spinning up a Streamlit runtime. Every helper here returns
plain frozen dataclasses (or ``None`` for empty states); the UI does
not have to special-case missing data — it just renders an "empty"
banner when the view-model field is ``None``.

Importing this package must NOT pull Streamlit in — keeping the
import graph clean lets the unit tests run without ``streamlit`` on
the path.
"""

from finskillos.ui.view_models.control_room_vm import (
    AlertSummary,
    ControlRoomViewModel,
    GoalSummary,
    GuardSummary,
    PortfolioSummaryVM,
    RegimeSummary,
    assert_view_model_is_safe,
    build_control_room_view_model,
)
from finskillos.ui.view_models.event_radar_vm import (
    EventLinkedNewsVM,
    EventLinkVM,
    EventRadarViewModel,
    EventRiskVM,
    assert_event_radar_view_model_is_safe,
    build_event_radar_view_model,
)
from finskillos.ui.view_models.index_lab_vm import (
    DEFAULT_INDEX_UNIVERSE,
    IndexInstrumentVM,
    IndexLabViewModel,
    IndexUniverseEntry,
    assert_index_lab_view_model_is_safe,
    build_index_lab_view_model,
)
from finskillos.ui.view_models.news_intelligence_vm import (
    NewsArticleVM,
    NewsImpactVM,
    NewsIntelligenceViewModel,
    assert_news_intelligence_view_model_is_safe,
    build_news_intelligence_view_model,
)
from finskillos.ui.view_models.symbol_lab_vm import (
    SymbolAlertVM,
    SymbolLabViewModel,
    SymbolNewsVM,
    SymbolPositionVM,
    SymbolRecentBarVM,
    SymbolTechnicalVM,
    assert_symbol_lab_view_model_is_safe,
    build_symbol_lab_view_model,
    normalize_ticker,
)

__all__ = [
    "AlertSummary",
    "ControlRoomViewModel",
    "DEFAULT_INDEX_UNIVERSE",
    "EventLinkVM",
    "EventLinkedNewsVM",
    "EventRadarViewModel",
    "EventRiskVM",
    "GoalSummary",
    "GuardSummary",
    "IndexInstrumentVM",
    "IndexLabViewModel",
    "IndexUniverseEntry",
    "NewsArticleVM",
    "NewsImpactVM",
    "NewsIntelligenceViewModel",
    "PortfolioSummaryVM",
    "RegimeSummary",
    "SymbolAlertVM",
    "SymbolLabViewModel",
    "SymbolNewsVM",
    "SymbolPositionVM",
    "SymbolRecentBarVM",
    "SymbolTechnicalVM",
    "assert_event_radar_view_model_is_safe",
    "assert_index_lab_view_model_is_safe",
    "assert_news_intelligence_view_model_is_safe",
    "assert_symbol_lab_view_model_is_safe",
    "assert_view_model_is_safe",
    "build_control_room_view_model",
    "build_event_radar_view_model",
    "build_index_lab_view_model",
    "build_news_intelligence_view_model",
    "build_symbol_lab_view_model",
    "normalize_ticker",
]
