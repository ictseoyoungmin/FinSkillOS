"""Slice 08 — Analysis Workspace page + dispatch smoke tests.

These tests do NOT spin up a real browser. They verify:

* The Analysis Workspace page module imports without pulling Streamlit
  at import time.
* App shell dispatches ``ANALYSIS_WORKSPACE`` to the new page (not the
  Slice-07 placeholder).
* Navigation metadata still exposes every OS-style label.
* The deferred placeholder for Analysis Workspace has been removed.
"""

from __future__ import annotations

import importlib
import inspect

from finskillos.ui.app_shell import NAV_ITEMS


def test_analysis_workspace_module_imports_without_streamlit() -> None:
    """Importing the page must not require ``streamlit`` on the path."""

    module = importlib.import_module("finskillos.ui.pages.analysis_workspace")
    assert hasattr(module, "render")


def test_nav_items_still_include_all_os_style_labels() -> None:
    labels = {label for _, label in NAV_ITEMS}
    required = {
        "Control Room",
        "Market Kernel",
        "Risk Firewall",
        "Mission Control",
        "Catalyst Watch",
        "Trade Memory",
        "Analysis Workspace",
        "System Ops",
    }
    assert required.issubset(labels)


def test_app_shell_dispatches_analysis_workspace_to_new_page() -> None:
    """Dispatch must route ``ANALYSIS_WORKSPACE`` to ``analysis_workspace``."""

    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    assert "analysis_workspace.render(session)" in source
    # And the Slice-07 placeholder is no longer called for this key.
    assert "deferred.render_analysis_workspace" not in source


def test_deferred_no_longer_exposes_analysis_workspace_placeholder() -> None:
    from finskillos.ui.pages import deferred

    assert not hasattr(deferred, "render_analysis_workspace")
    # Other placeholders remain in place.
    assert hasattr(deferred, "render_catalyst_watch")
    assert hasattr(deferred, "render_trade_memory")
