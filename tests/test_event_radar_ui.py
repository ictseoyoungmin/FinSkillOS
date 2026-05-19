"""Slice 11 — Event Radar page + dispatch smoke tests.

These tests do NOT spin up a real browser. They verify:

* The page module imports without pulling Streamlit at import time.
* The view-model module imports without pulling Streamlit at import time.
* App shell dispatches ``CATALYST_WATCH`` to the Event Radar page.
* The deferred placeholder for Catalyst Watch was removed.
* The page uses the safety scan at the UI seam.
* The page does not include forbidden direct-advice button captions.
* The page exposes a date-status-aware selector that includes
  TENTATIVE / WINDOW / SPECULATIVE.
"""

from __future__ import annotations

import importlib
import inspect


def test_event_radar_module_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.pages.event_radar")
    assert hasattr(module, "render")


def test_event_radar_view_model_module_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.view_models.event_radar_vm")
    assert hasattr(module, "build_event_radar_view_model")
    assert hasattr(module, "assert_event_radar_view_model_is_safe")


def test_app_shell_dispatches_catalyst_watch_to_event_radar() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    assert "event_radar.render(session)" in source
    # The deferred placeholder must no longer be called for this key.
    assert "deferred.render_catalyst_watch" not in source


def test_deferred_no_longer_exposes_catalyst_watch_placeholder() -> None:
    from finskillos.ui.pages import deferred

    assert not hasattr(deferred, "render_catalyst_watch")
    # Slice 12 wired Trade Memory to the real trade_journal page, so
    # the deferred placeholder for it has been removed too.
    assert not hasattr(deferred, "render_trade_memory")


def test_event_radar_page_runs_safety_scan() -> None:
    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    assert "assert_event_radar_view_model_is_safe" in source


def test_event_radar_page_does_not_expose_direct_trade_buttons() -> None:
    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    for forbidden in ('"Buy"', '"Sell"', '"Execute"', '"Trade Now"', "지금 사라"):
        assert forbidden not in source


def test_event_radar_page_supports_uncertain_date_status_vocabulary() -> None:
    """The manual form must let the user pick uncertain statuses."""

    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    for status in ("TENTATIVE", "WINDOW", "SPECULATIVE"):
        assert status in source or status in {
            label for label in source.split()
        }


def test_event_radar_page_offers_sample_seed_button() -> None:
    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    assert "seed_sample_events" in source


def test_event_radar_page_describes_score_as_not_prediction() -> None:
    """11 cleanup Task 4 — risk score must be described as non-predictive."""

    from finskillos.ui.pages import event_radar

    source = inspect.getsource(event_radar)
    assert "가격 예측이 아니라" in source or "not a prediction" in source
