"""Slice 09 — Symbol Lab page + dispatch smoke tests.

These tests do NOT spin up a real browser. They verify:

* The Symbol Lab page module imports without pulling Streamlit at
  import time.
* App shell dispatches ``SYMBOL_LAB`` to the new page module.
* Navigation metadata exposes the new ``Symbol Lab`` label.
* The page module uses the safety scan at the UI seam.
* The page does not include forbidden direct-advice button captions.
"""

from __future__ import annotations

import importlib
import inspect

from finskillos.ui.app_shell import NAV_ITEMS


def test_symbol_lab_module_imports_without_streamlit() -> None:
    """Importing the page must not require ``streamlit`` on the path."""

    module = importlib.import_module("finskillos.ui.pages.symbol_lab")
    assert hasattr(module, "render")


def test_symbol_lab_view_model_module_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.view_models.symbol_lab_vm")
    assert hasattr(module, "build_symbol_lab_view_model")
    assert hasattr(module, "assert_symbol_lab_view_model_is_safe")


def test_nav_items_include_symbol_lab() -> None:
    labels = {label for _, label in NAV_ITEMS}
    assert "Symbol Lab" in labels


def test_symbol_lab_nav_key_is_unique() -> None:
    keys = [key for key, _ in NAV_ITEMS]
    assert "SYMBOL_LAB" in keys
    assert len(keys) == len(set(keys))


def test_symbol_lab_appears_after_analysis_workspace() -> None:
    keys = [key for key, _ in NAV_ITEMS]
    assert keys.index("SYMBOL_LAB") == keys.index("ANALYSIS_WORKSPACE") + 1


def test_app_shell_dispatches_symbol_lab_to_new_page() -> None:
    """Dispatch must route ``SYMBOL_LAB`` to ``symbol_lab.render``."""

    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    assert "symbol_lab.render(session)" in source


def test_symbol_lab_page_runs_safety_scan() -> None:
    from finskillos.ui.pages import symbol_lab

    source = inspect.getsource(symbol_lab)
    assert "assert_symbol_lab_view_model_is_safe" in source


def test_symbol_lab_page_does_not_expose_direct_trade_buttons() -> None:
    from finskillos.ui.pages import symbol_lab

    source = inspect.getsource(symbol_lab)
    # Forbidden labels — never let the page ship a transaction trigger.
    for forbidden in ('"Buy"', '"Sell"', '"Execute"', '"Trade Now"', "지금 사라"):
        assert forbidden not in source


def test_symbol_lab_page_marks_chart_as_deferred() -> None:
    from finskillos.ui.pages import symbol_lab

    source = inspect.getsource(symbol_lab)
    assert "이연" in source or "deferred" in source.lower()
