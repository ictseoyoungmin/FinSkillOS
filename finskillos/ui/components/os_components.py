"""Reusable OS-style component helpers — Slice 13.5.

These wrap small pieces of CSS-styled HTML (defined in
:mod:`finskillos.ui.theme`) so pages can render consistent panels /
metric tiles / badges / empty states without duplicating markup.

Streamlit is imported lazily inside each function. The module stays
importable in non-Streamlit test contexts.

Tone vocabulary (mirrors :mod:`finskillos.ui.theme`):

    neutral · info · success · warning · danger
    cyan · amber · green · red · purple
"""

from __future__ import annotations

from finskillos.ui.theme import tone_to_token


def os_badge_html(text: str, *, tone: str = "neutral") -> str:
    """Return raw HTML for a tone-coloured pill badge.

    Useful when assembling badges inside an ``st.markdown`` block —
    ``os_badge`` is the Streamlit-bound variant that writes directly
    to the page.
    """

    token = tone_to_token(tone)
    pill_class = (
        f"fso-pill fso-pill-{token}"
        if token in {"cyan", "amber", "green", "red"}
        else "fso-pill fso-pill-muted"
    )
    return f'<span class="{pill_class}">{text}</span>'


def os_badge(text: str, *, tone: str = "neutral") -> None:
    import streamlit as st

    st.markdown(os_badge_html(text, tone=tone), unsafe_allow_html=True)


def os_panel(
    title: str,
    *,
    subtitle: str | None = None,
    status: str | None = None,
    status_tone: str = "neutral",
) -> None:
    """Render a titled OS-style panel header.

    Use it directly above a group of ``st.metric`` / ``st.dataframe``
    calls — the panel is a header card; downstream Streamlit widgets
    visually sit underneath it.
    """

    import streamlit as st

    status_html = (
        os_badge_html(status, tone=status_tone)
        if status
        else ""
    )
    subtitle_html = (
        f'<div class="fso-panel-subtitle">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div class="fso-panel">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div class="fso-panel-title">{title}</div>
                <div>{status_html}</div>
            </div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def os_section_header(title: str, *, eyebrow: str | None = None) -> None:
    """Render a uppercase section header with an optional eyebrow tag.

    Designed for top-of-section markers, e.g.
    ``os_section_header("Tape Strength", eyebrow="Index Lab v0")``.
    """

    import streamlit as st

    eyebrow_html = (
        f'<div class="fso-section-eyebrow">{eyebrow}</div>'
        if eyebrow
        else ""
    )
    st.markdown(
        f"""
        <div style="margin: 8px 0 4px;">
            {eyebrow_html}
            <div class="fso-section-title">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def os_empty_state(title: str, message: str) -> None:
    """Render a standardised empty-state block.

    Use this to answer "what is missing / why is this empty / what
    safe next step exists" in one block instead of bare ``st.info``
    captions.
    """

    import streamlit as st

    st.markdown(
        f"""
        <div class="fso-empty">
            <div class="fso-empty-title">{title}</div>
            <div class="fso-empty-msg">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def os_metric(
    label: str,
    value: str,
    *,
    delta: str | None = None,
    tone: str = "neutral",
) -> None:
    """Streamlit metric tile with tone-aware delta colouring.

    Falls back to :func:`streamlit.metric` so existing rendering rules
    (formatting, screen-reader handling) stay intact. The ``tone``
    argument controls the delta colour via the standard Streamlit
    ``delta_color`` API: ``success`` / ``green`` → normal, ``danger``
    / ``red`` → inverse, anything else → off.
    """

    import streamlit as st

    delta_color: str
    if tone in {"success", "green"}:
        delta_color = "normal"
    elif tone in {"danger", "red"}:
        delta_color = "inverse"
    else:
        delta_color = "off"

    st.metric(label, value, delta=delta, delta_color=delta_color)


__all__ = [
    "os_badge",
    "os_badge_html",
    "os_empty_state",
    "os_metric",
    "os_panel",
    "os_section_header",
]
