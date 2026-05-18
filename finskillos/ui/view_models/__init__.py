"""Slice-07 UI view models — DB-backed, Streamlit-free read models.

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

__all__ = [
    "AlertSummary",
    "ControlRoomViewModel",
    "GoalSummary",
    "GuardSummary",
    "PortfolioSummaryVM",
    "RegimeSummary",
    "assert_view_model_is_safe",
    "build_control_room_view_model",
]
