"""Slice 10 — News Intelligence page + dispatch smoke tests.

These tests do NOT spin up a real browser. They verify:

* The page module imports without pulling Streamlit at import time.
* App shell dispatches ``NEWS_INTELLIGENCE`` to the new page module.
* Navigation metadata exposes the new ``News Intelligence`` label.
* The page uses the safety scan at the UI seam.
* The page does not include forbidden direct-advice button captions.
* The page does not advertise long article body rendering.
"""

from __future__ import annotations

import importlib
import inspect

from finskillos.ui.app_shell import NAV_ITEMS


def test_news_intelligence_module_imports_without_streamlit() -> None:
    module = importlib.import_module("finskillos.ui.pages.news_intelligence")
    assert hasattr(module, "render")


def test_news_intelligence_view_model_module_imports_without_streamlit() -> None:
    module = importlib.import_module(
        "finskillos.ui.view_models.news_intelligence_vm"
    )
    assert hasattr(module, "build_news_intelligence_view_model")
    assert hasattr(module, "assert_news_intelligence_view_model_is_safe")


def test_nav_items_include_news_intelligence() -> None:
    labels = {label for _, label in NAV_ITEMS}
    assert "News Intelligence" in labels


def test_news_intelligence_nav_key_is_unique() -> None:
    keys = [key for key, _ in NAV_ITEMS]
    assert "NEWS_INTELLIGENCE" in keys
    assert len(keys) == len(set(keys))


def test_app_shell_dispatches_news_intelligence_to_new_page() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    assert "news_intelligence.render(session)" in source


def test_news_intelligence_page_runs_safety_scan() -> None:
    from finskillos.ui.pages import news_intelligence

    source = inspect.getsource(news_intelligence)
    assert "assert_news_intelligence_view_model_is_safe" in source


def test_news_intelligence_page_does_not_expose_direct_trade_buttons() -> None:
    from finskillos.ui.pages import news_intelligence

    source = inspect.getsource(news_intelligence)
    for forbidden in ('"Buy"', '"Sell"', '"Execute"', '"Trade Now"', "지금 사라"):
        assert forbidden not in source


def test_news_intelligence_page_does_not_render_full_article_body() -> None:
    from finskillos.ui.pages import news_intelligence

    source = inspect.getsource(news_intelligence)
    # Manual entry form must NOT ask for full body — only short summary.
    assert "Full article body" not in source
    assert "article_body" not in source
    assert "full_text" not in source
    # And the help-text reinforces that point.
    assert "원문 전체가 아닌" in source or "Short summary" in source


def test_news_intelligence_manual_form_caps_summary_length() -> None:
    """The Streamlit form should hard-cap summary entry to MAX_SUMMARY_CHARS."""

    from finskillos.ui.pages import news_intelligence

    source = inspect.getsource(news_intelligence)
    assert "max_chars=500" in source
