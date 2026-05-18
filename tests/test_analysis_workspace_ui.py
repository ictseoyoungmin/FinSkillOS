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
        "Symbol Lab",
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


# ---------------------------------------------------------------------------
# 08 cleanup — scope boundary + copy consistency
# ---------------------------------------------------------------------------


def test_analysis_workspace_copy_does_not_reference_missing_system_ops_actions() -> None:
    """08 cleanup Task 2 — page must not instruct the user to use absent actions."""

    from finskillos.ui.pages import analysis_workspace

    source = inspect.getsource(analysis_workspace)
    assert "Market Refresh / Indicators 재계산을 실행" not in source
    assert "Market Refresh" not in source
    # Updated copy must signal the read-only behaviour.
    assert "자동 refresh는 수행하지 않습니다" in source or "읽는 전용 뷰" in source


def test_slice_08_completion_notes_mark_chart_items_deferred() -> None:
    """08 cleanup Task 4 — .devmd/08 must label scope as v0 + deferred chart items."""

    from pathlib import Path

    text = Path(".devmd/08_Research_Hub_Index_Lab.md").read_text(encoding="utf-8")
    assert "DONE_AS_INDEX_LAB_V0" in text
    assert "normalized overlay chart" in text
    assert "indicator toggles" in text
    # The scope-note language must explicitly call out the deferral.
    assert "deferred" in text.lower()
