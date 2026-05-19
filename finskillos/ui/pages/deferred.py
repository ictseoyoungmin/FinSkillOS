"""Placeholder pages for tabs scheduled in later slices.

Each renderer is a small, descriptive stub so the OS-style navigation
shell stays complete and consistent without faking functionality that
has not been built yet.
"""

from __future__ import annotations


def render_trade_memory() -> None:
    import streamlit as st

    st.markdown("## Trade Memory")
    st.info(
        "Trade Memory는 Slice 12 Trade Journal에서 활성화됩니다. "
        "매매 thesis / 복기 / regime별 성과가 누적되면 표시됩니다."
    )


# NOTE: Analysis Workspace was a placeholder in Slice 07; Slice 08 wires
# it to the real Index Lab page (``finskillos.ui.pages.analysis_workspace``).
# Symbol Lab was a placeholder until Slice 09; News Intelligence was a
# placeholder until Slice 10; Catalyst Watch was a placeholder until
# Slice 11 wired it to ``finskillos.ui.pages.event_radar``.
# Only Trade Memory remains deferred (Slice 12).
