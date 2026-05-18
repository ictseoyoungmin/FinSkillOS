"""Slice 07 — Streamlit shell smoke tests.

These tests do NOT spin up a real browser. They verify:

* The Streamlit entry point (``app.py`` + ``finskillos.ui.app_shell``)
  imports cleanly in a non-Streamlit context.
* Page modules import without pulling Streamlit at import time.
* Navigation metadata exposes the OS-style tab labels Slice 07 promises.
* Formatting helpers behave on the values the cards will actually render.
"""

from __future__ import annotations

import importlib

import pytest

from finskillos.ui.app_shell import NAV_ITEMS
from finskillos.ui.components.formatting import (
    format_krw,
    format_pct,
    format_ratio,
    risk_color,
    status_emoji,
    status_label,
)

# ---------------------------------------------------------------------------
# Entrypoint / module imports
# ---------------------------------------------------------------------------


def test_app_entry_point_imports_without_streamlit() -> None:
    module = importlib.import_module("app")
    assert hasattr(module, "__name__")


@pytest.mark.parametrize(
    "module_name",
    [
        "finskillos.ui.app_shell",
        "finskillos.ui.pages.control_room",
        "finskillos.ui.pages.market_kernel",
        "finskillos.ui.pages.risk_firewall",
        "finskillos.ui.pages.mission_control",
        "finskillos.ui.pages.system_ops",
        "finskillos.ui.pages.deferred",
        "finskillos.ui.pages.analysis_workspace",
        "finskillos.ui.pages.symbol_lab",
        "finskillos.ui.components.cards",
        "finskillos.ui.components.formatting",
        "finskillos.ui.view_models",
        "finskillos.ui.view_models.control_room_vm",
        "finskillos.ui.view_models.index_lab_vm",
        "finskillos.ui.view_models.symbol_lab_vm",
    ],
)
def test_ui_modules_import_without_streamlit(module_name: str) -> None:
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# Navigation metadata
# ---------------------------------------------------------------------------


def test_nav_items_contain_os_style_labels() -> None:
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


def test_nav_keys_are_unique() -> None:
    keys = [key for key, _ in NAV_ITEMS]
    assert len(keys) == len(set(keys))


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def test_format_krw_handles_none_and_value() -> None:
    assert format_krw(None) == "—"
    assert format_krw(57000000) == "57,000,000 KRW"


def test_format_pct_handles_none_and_value() -> None:
    assert format_pct(None) == "—"
    assert format_pct(57.5) == "57.5%"


def test_format_ratio_renders_zero_to_one_as_percent() -> None:
    assert format_ratio(0.35) == "35.0%"


def test_risk_color_has_distinct_colors_per_level() -> None:
    colors = {
        risk_color("GREEN"),
        risk_color("YELLOW"),
        risk_color("ORANGE"),
        risk_color("RED"),
    }
    assert len(colors) == 4


def test_status_label_translates_known_statuses() -> None:
    assert status_label("PASS") == "정상"
    assert status_label("FAIL") == "경고"
    assert status_label("UNKNOWN") == "UNKNOWN"  # falls back to raw value


def test_status_emoji_returns_compact_symbol() -> None:
    assert status_emoji("PASS") == "✓"
    assert status_emoji("FAIL") == "✕"
    assert status_emoji("INFO") == "•"


# ---------------------------------------------------------------------------
# 07 cleanup — null-session fallback + system-ops helpers
# ---------------------------------------------------------------------------


def test_null_session_is_not_dispatchable() -> None:
    """07-cleanup Task 2 — _NullSession must not be handed to a page renderer."""

    from finskillos.ui.app_shell import _can_dispatch, _NullSession

    assert _can_dispatch(_NullSession()) is False


def test_real_objects_are_dispatchable() -> None:
    from finskillos.ui.app_shell import _can_dispatch

    class _FakeSession:
        pass

    assert _can_dispatch(_FakeSession()) is True
    assert _can_dispatch(object()) is True


def test_null_session_raises_loudly_if_a_page_ever_uses_it() -> None:
    """Last-resort guard — page code that reaches a NullSession must fail loudly."""

    from finskillos.ui.app_shell import _NullSession

    session = _NullSession()
    with pytest.raises(RuntimeError):
        session.query  # noqa: B018 — triggers __getattr__


def test_format_regime_recalc_message_includes_key_fields() -> None:
    """07-cleanup Task 4 — System Ops Regime 재계산 success line is unit-testable."""

    from decimal import Decimal

    from finskillos.ui.pages.system_ops import format_regime_recalc_message

    msg = format_regime_recalc_message(
        regime="RISK_ON_OVERHEAT",
        confidence=Decimal("82"),
        decision_mode="HOLD_WINNERS",
        risk_level="YELLOW",
    )
    assert "RISK_ON_OVERHEAT" in msg
    assert "82" in msg
    assert "HOLD_WINNERS" in msg
    assert "YELLOW" in msg
    # Safety: even the success message must not leak direct-advice wording.
    from finskillos.guards import GuardResult, assert_no_forbidden_wording

    assert_no_forbidden_wording(
        GuardResult(
            guard_name="TEST",
            status="INFO",
            risk_level="GREEN",
            title="",
            message=msg,
        )
    )


def test_risk_firewall_caption_does_not_claim_auto_persist() -> None:
    """07-cleanup Task 3 — copy must not say WARN+ alerts auto-accumulate on read-only render."""

    import inspect

    from finskillos.ui.pages import risk_firewall

    source = inspect.getsource(risk_firewall)
    assert "자동으로 alerts 테이블에 누적" not in source
    assert "읽기 전용" in source or "Risk Guard 재실행" in source
