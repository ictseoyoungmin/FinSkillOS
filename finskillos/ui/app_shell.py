"""FinSkillOS Streamlit shell — Slice-07 Control Room cockpit.

Provides the OS-style top navigation (Control Room / Market Kernel /
Risk Firewall / Mission Control / Catalyst Watch / Trade Memory /
Analysis Workspace / Symbol Lab / System Ops) and dispatches to
per-page render functions.

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
    ("SYMBOL_LAB", "Symbol Lab"),
    ("NEWS_INTELLIGENCE", "News Intelligence"),
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
        if not _can_dispatch(session):
            # The friendly DB-error banner already rendered inside
            # _session_scope; stop here so no page renderer ever runs
            # against the _NullSession sentinel (07-cleanup Task 2).
            return
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
        analysis_workspace,
        control_room,
        deferred,
        market_kernel,
        mission_control,
        news_intelligence,
        risk_firewall,
        symbol_lab,
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
        analysis_workspace.render(session)
    elif nav_key == "SYMBOL_LAB":
        symbol_lab.render(session)
    elif nav_key == "NEWS_INTELLIGENCE":
        news_intelligence.render(session)
    else:
        import streamlit as st

        st.warning(f"Unknown navigation key: {nav_key}")


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


@contextmanager
def _session_scope() -> Iterator[object]:  # pragma: no cover - thin DB wrapper
    """Yield a DB session for the page render after a preflight check.

    Startup failures (missing module, bad URL, unreachable DB) are
    surfaced as a Streamlit-friendly error banner and a ``_NullSession``
    is yielded EXACTLY ONCE so the contextmanager does not raise
    ``RuntimeError: generator didn't stop after throw()``.

    Once the real session is yielded we never yield again — exceptions
    raised while a page renders are allowed to propagate so Streamlit's
    own error handling kicks in, with rollback / close happening in the
    ``finally`` block.
    """

    import streamlit as st
    from sqlalchemy import text

    try:
        from finskillos.db.session import get_session_factory

        session = get_session_factory()()
    except Exception as exc:  # noqa: BLE001 — display configuration errors gracefully
        st.error(f"DB 세션 모듈을 불러올 수 없습니다: {exc}")
        yield _NullSession()
        return

    # Preflight: a cheap round-trip catches bad DATABASE_URLs / missing
    # migrations BEFORE we hand the session to a page. Doing it here
    # means the yield below only ever runs against a known-good session.
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        session.close()
        st.error(
            "DB 연결에 실패했습니다. DATABASE_URL 설정과 alembic upgrade head 실행 "
            f"여부를 확인하세요.\n\n오류: {exc}"
        )
        yield _NullSession()
        return

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class _NullSession:
    """Sentinel yielded when the DB session cannot be created.

    The Streamlit shell checks with ``_can_dispatch`` BEFORE handing the
    object to a page renderer, so under normal operation no page ever
    touches a ``_NullSession``. ``__getattr__`` still raises loudly as a
    last-resort guard against future code paths that forget the check.
    """

    def __getattr__(self, name):  # type: ignore[no-untyped-def]
        raise RuntimeError(
            "Streamlit page tried to use the DB session after a connection error."
        )


def _can_dispatch(session: object) -> bool:
    """True if ``session`` is a real DB session safe to hand to a page.

    Pure helper kept module-level so unit tests can verify the fallback
    decision without spinning up Streamlit (07-cleanup Task 2).
    """

    return not isinstance(session, _NullSession)


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
