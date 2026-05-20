"""Slice 13.5 — OS UI Polish source-level smoke tests.

These tests inspect the new theme + os_components modules and the
app-shell wiring **without** spinning up Streamlit. They verify:

* ``finskillos.ui.theme`` and ``finskillos.ui.components.os_components``
  import without Streamlit side effects.
* The theme module exposes the required public API (``THEME_*``,
  ``ALL_THEMES``, ``THEME_TOKENS``, ``build_os_css``, ``apply_os_theme``,
  ``render_os_header``, ``render_theme_selector``).
* ``build_os_css`` for every supported theme contains the core OS
  CSS variables (``--fso-bg`` / ``--fso-panel`` / ``--fso-cyan`` /
  ``--fso-amber`` / ``--fso-red``).
* App shell now calls ``apply_os_theme`` + ``render_os_header`` and
  the sidebar source instantiates the theme selector.
* All ten main OS nav labels still route to real page modules; no
  main route dispatches to a deferred placeholder.
* Every page module still exposes ``render()`` and imports without
  Streamlit at import time.
* Page sources do not introduce direct-execution button captions.
* The Slice-13 safety acceptance gate still passes (smoke import).
"""

from __future__ import annotations

import importlib
import inspect

import pytest

# ---------------------------------------------------------------------------
# Theme module surface
# ---------------------------------------------------------------------------


def test_theme_module_imports_without_streamlit_side_effects() -> None:
    module = importlib.import_module("finskillos.ui.theme")
    # Streamlit-bound helpers must NOT pull streamlit at import time.
    assert "streamlit" not in inspect.getsource(module).split("\n", 1)[0]
    assert hasattr(module, "apply_os_theme")
    assert hasattr(module, "build_os_css")
    assert hasattr(module, "render_os_header")
    assert hasattr(module, "render_status_strip")
    assert hasattr(module, "render_theme_selector")


def test_theme_module_exposes_required_constants() -> None:
    from finskillos.ui import theme

    assert theme.THEME_DARK == "dark"
    assert theme.THEME_LIGHT == "light"
    assert theme.THEME_MATERIAL == "material"
    assert theme.ALL_THEMES == ("dark", "light", "material")
    assert set(theme.THEME_TOKENS.keys()) == {"dark", "light", "material"}


def test_os_components_module_imports_without_streamlit_side_effects() -> None:
    module = importlib.import_module("finskillos.ui.components.os_components")
    assert hasattr(module, "os_badge")
    assert hasattr(module, "os_badge_html")
    assert hasattr(module, "os_empty_state")
    assert hasattr(module, "os_metric")
    assert hasattr(module, "os_panel")
    assert hasattr(module, "os_section_header")


# ---------------------------------------------------------------------------
# CSS builder
# ---------------------------------------------------------------------------


_REQUIRED_TOKENS = (
    "--fso-bg",
    "--fso-panel",
    "--fso-cyan",
    "--fso-amber",
    "--fso-red",
)


@pytest.mark.parametrize("theme", ["dark", "light", "material"])
def test_build_os_css_contains_required_tokens(theme: str) -> None:
    from finskillos.ui.theme import build_os_css

    css = build_os_css(theme)
    for token in _REQUIRED_TOKENS:
        assert token in css, f"theme {theme!r} CSS missing token {token!r}"


def test_build_os_css_emits_data_theme_attribute() -> None:
    from finskillos.ui.theme import build_os_css

    assert 'data-theme="dark"' in build_os_css("dark")
    assert 'data-theme="light"' in build_os_css("light")
    assert 'data-theme="material"' in build_os_css("material")


def test_build_os_css_falls_back_to_dark_for_unknown_theme() -> None:
    from finskillos.ui.theme import build_os_css

    css = build_os_css("not-a-real-theme")
    assert 'data-theme="dark"' in css


def test_dark_theme_uses_cyan_accent_token() -> None:
    from finskillos.ui.theme import THEME_DARK, THEME_TOKENS

    assert THEME_TOKENS[THEME_DARK]["cyan"].lower() == "#00e5ff"


def test_tone_to_token_maps_vocabulary_to_palette_tokens() -> None:
    from finskillos.ui.theme import tone_to_token

    assert tone_to_token("success") == "green"
    assert tone_to_token("danger") == "red"
    assert tone_to_token("warning") == "amber"
    assert tone_to_token("info") == "cyan"
    assert tone_to_token("neutral") == "muted"
    assert tone_to_token("not-a-tone") == "muted"


# ---------------------------------------------------------------------------
# App shell wiring
# ---------------------------------------------------------------------------


def test_app_shell_applies_os_theme() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell)
    assert "apply_os_theme" in source
    assert "render_os_header" in source


def test_app_shell_sidebar_renders_theme_selector() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._render_sidebar)
    assert "render_theme_selector" in source


def test_app_shell_dispatch_routes_all_main_os_tabs_to_real_pages() -> None:
    from finskillos.ui import app_shell

    source = inspect.getsource(app_shell._dispatch)
    expected_fragments = (
        "control_room.render(session)",
        "market_kernel.render(session)",
        "risk_firewall.render(session)",
        "mission_control.render(session)",
        "analysis_workspace.render(session)",
        "symbol_lab.render(session)",
        "news_intelligence.render(session)",
        "event_radar.render(session)",
        "trade_journal.render(session)",
        "system_ops.render(session)",
    )
    for fragment in expected_fragments:
        assert fragment in source, f"dispatch missing {fragment!r}"
    # No main route should still dispatch to a deferred placeholder.
    assert "deferred.render_catalyst_watch" not in source
    assert "deferred.render_trade_memory" not in source
    assert "deferred.render_analysis_workspace" not in source


def test_app_shell_nav_items_still_cover_main_os_tabs() -> None:
    from finskillos.ui.app_shell import NAV_ITEMS

    labels = {label for _, label in NAV_ITEMS}
    required = {
        "Control Room",
        "Market Kernel",
        "Risk Firewall",
        "Mission Control",
        "Analysis Workspace",
        "Symbol Lab",
        "News Intelligence",
        "Catalyst Watch",
        "Trade Memory",
        "System Ops",
    }
    assert required.issubset(labels)


# ---------------------------------------------------------------------------
# Page modules — still importable + still expose render() + no exec buttons
# ---------------------------------------------------------------------------


_MAIN_PAGE_MODULES: tuple[str, ...] = (
    "finskillos.ui.pages.control_room",
    "finskillos.ui.pages.market_kernel",
    "finskillos.ui.pages.risk_firewall",
    "finskillos.ui.pages.mission_control",
    "finskillos.ui.pages.analysis_workspace",
    "finskillos.ui.pages.symbol_lab",
    "finskillos.ui.pages.news_intelligence",
    "finskillos.ui.pages.event_radar",
    "finskillos.ui.pages.trade_journal",
    "finskillos.ui.pages.system_ops",
)


@pytest.mark.parametrize("module_name", _MAIN_PAGE_MODULES)
def test_page_module_imports_without_streamlit_and_exposes_render(
    module_name: str,
) -> None:
    module = importlib.import_module(module_name)
    assert hasattr(module, "render")


@pytest.mark.parametrize("module_name", _MAIN_PAGE_MODULES)
def test_page_source_has_no_direct_execution_button_captions(
    module_name: str,
) -> None:
    module = importlib.import_module(module_name)
    source = inspect.getsource(module)
    forbidden = (
        '"Buy"',
        '"Sell"',
        '"Execute"',
        '"Trade Now"',
        "지금 사라",
        "지금 팔아라",
        "매수 버튼",
        "매도 버튼",
    )
    for caption in forbidden:
        assert caption not in source, (
            f"{module_name} introduces forbidden execution caption {caption!r}"
        )


# ---------------------------------------------------------------------------
# Safety acceptance smoke (sanity — Slice 13 suite should still load)
# ---------------------------------------------------------------------------


def test_acceptance_safety_language_suite_still_importable() -> None:
    """Importing the Slice-13 safety acceptance suite must still succeed.

    Polish slice must not break the safety contract — a failing
    import here would mean we accidentally moved / renamed
    ``assert_no_forbidden_wording`` or the related test helpers.
    """

    module = importlib.import_module("tests.test_acceptance_safety_language")
    assert hasattr(module, "test_acceptance_forbidden_phrases_are_blocked")
    assert hasattr(module, "test_acceptance_descriptive_phrases_remain_allowed")
