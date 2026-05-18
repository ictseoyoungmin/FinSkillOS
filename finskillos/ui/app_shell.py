"""FinSkillOS Streamlit shell — Slice-07 Control Room cockpit.

Provides the OS-style top navigation (Control Room / Market Kernel /
Risk Firewall / Mission Control / Catalyst Watch / Trade Memory /
Analysis Workspace / System Ops) and dispatches to per-page render
functions.

Streamlit + SQLAlchemy session imports are kept inside ``run_app`` so
``import finskillos.ui.app_shell`` stays cheap and remains importable
in unit tests that do not have a Streamlit runtime.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("CONTROL_ROOM", "Control Room"),
    ("MARKET_KERNEL", "Market Kernel"),
    ("RISK_FIREWALL", "Risk Firewall"),
    ("MISSION_CONTROL", "Mission Control"),
    ("CATALYST_WATCH", "Catalyst Watch"),
    ("TRADE_MEMORY", "Trade Memory"),
    ("ANALYSIS_WORKSPACE", "Analysis Workspace"),
    ("SYSTEM_OPS", "System Ops"),
)


def run_app() -> None:
    """Render the FinSkillOS Streamlit shell."""

    import streamlit as st

    st.set_page_config(
        page_title="FinSkillOS · Control Room",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_global_styles()
    _render_header()

    nav_key = _render_sidebar()

    with _session_scope() as session:
        _dispatch(nav_key, session)


# ---------------------------------------------------------------------------
# Layout + navigation
# ---------------------------------------------------------------------------


def _render_header() -> None:
    import streamlit as st

    st.markdown(
        """
        <div style="display:flex; align-items:baseline; justify-content:space-between;
             padding:6px 4px 14px; border-bottom:1px solid rgba(255,255,255,0.06);
             margin-bottom:18px;">
            <div>
                <div style="font-family:'Space Grotesk',sans-serif; font-size:22px;
                     font-weight:700; color:#00e5ff; letter-spacing:0.12em;">
                    FINSKILLOS
                </div>
                <div style="font-size:11px; color:#6090b8; letter-spacing:0.3em;">
                    v2.1 · CONTROL ROOM
                </div>
            </div>
            <div style="font-size:11px; color:#6090b8; letter-spacing:0.2em;">
                US MARKET FOCUS · INTERPRETATION FIRST
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> str:
    import streamlit as st

    labels = [label for _, label in NAV_ITEMS]
    keys = [key for key, _ in NAV_ITEMS]

    with st.sidebar:
        st.markdown(
            """
            <div style="font-size:11px; color:#6090b8; letter-spacing:0.25em;
                 margin-bottom:8px;">
                NAV
            </div>
            """,
            unsafe_allow_html=True,
        )
        selected_label = st.radio(
            "Navigation",
            labels,
            index=0,
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(
            "FinSkillOS는 투자 자문 도구가 아니며, 매수 / 매도 지시를 제공하지 않습니다."
        )

    return keys[labels.index(selected_label)]


def _dispatch(nav_key: str, session) -> None:  # type: ignore[no-untyped-def]
    from finskillos.ui.pages import (
        control_room,
        deferred,
        market_kernel,
        mission_control,
        risk_firewall,
        system_ops,
    )

    if nav_key == "CONTROL_ROOM":
        control_room.render(session)
    elif nav_key == "MARKET_KERNEL":
        market_kernel.render(session)
    elif nav_key == "RISK_FIREWALL":
        risk_firewall.render(session)
    elif nav_key == "MISSION_CONTROL":
        mission_control.render(session)
    elif nav_key == "SYSTEM_OPS":
        system_ops.render(session)
    elif nav_key == "CATALYST_WATCH":
        deferred.render_catalyst_watch()
    elif nav_key == "TRADE_MEMORY":
        deferred.render_trade_memory()
    elif nav_key == "ANALYSIS_WORKSPACE":
        deferred.render_analysis_workspace()
    else:
        import streamlit as st

        st.warning(f"Unknown navigation key: {nav_key}")


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@contextmanager
def _session_scope() -> Iterator[object]:  # pragma: no cover - thin DB wrapper
    """Yield a DB session for the page render.

    Wraps ``finskillos.db.session.session_scope`` but converts startup
    failures (missing DB, bad URL, etc.) into a Streamlit-friendly
    error banner so the app does not crash on first launch.
    """

    import streamlit as st

    try:
        from finskillos.db.session import session_scope
    except Exception as exc:  # noqa: BLE001 — display configuration errors gracefully
        st.error(f"DB 세션 모듈을 불러올 수 없습니다: {exc}")
        yield _NullSession()
        return

    try:
        with session_scope() as session:
            yield session
    except Exception as exc:  # noqa: BLE001
        st.error(
            "DB 연결에 실패했습니다. DATABASE_URL 설정과 alembic upgrade head 실행 "
            f"여부를 확인하세요.\n\n오류: {exc}"
        )
        yield _NullSession()


class _NullSession:
    """Tiny fallback so page renderers can still call session methods.

    Pages should never reach a code path that requires a real session
    once the error banner above fires; this stub exists only so a
    misconfigured environment never crashes the Streamlit process.
    """

    def __getattr__(self, name):  # type: ignore[no-untyped-def]
        raise RuntimeError(
            "Streamlit page tried to use the DB session after a connection error."
        )


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


def _inject_global_styles() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
            section.main > div { padding-top: 0.4rem; }
            h2, h3, h4 { letter-spacing: 0.02em; }
            div[data-testid="stMetricValue"] {
                font-family: 'JetBrains Mono', monospace;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
