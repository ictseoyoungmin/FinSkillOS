"""Placeholder pages for tabs scheduled in later slices.

Each renderer is a small, descriptive stub so the OS-style navigation
shell stays complete and consistent without faking functionality that
has not been built yet.
"""

from __future__ import annotations


def render_catalyst_watch() -> None:
    import streamlit as st

    st.markdown("## Catalyst Watch")
    st.info(
        "Catalyst Watch는 Slice 11 Event Radar에서 활성화됩니다. "
        "이벤트 / 실적 / FOMC 데이터가 수집되면 자동으로 표시됩니다."
    )


def render_trade_memory() -> None:
    import streamlit as st

    st.markdown("## Trade Memory")
    st.info(
        "Trade Memory는 Slice 12 Trade Journal에서 활성화됩니다. "
        "매매 thesis / 복기 / regime별 성과가 누적되면 표시됩니다."
    )


# NOTE: Analysis Workspace was a placeholder in Slice 07; Slice 08 wires
# it to the real Index Lab page (``finskillos.ui.pages.analysis_workspace``).
# The placeholder was removed; Symbol Lab / News Intelligence remain
# deferred to later slices.
