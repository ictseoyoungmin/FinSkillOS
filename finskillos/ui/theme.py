"""FinSkillOS OS-style theme layer — Slice 13.5.

A single source of truth for visual identity across all Streamlit
pages. The module is intentionally Streamlit-lazy: tests can import
it without ``streamlit`` on the path because the actual ``st.``
calls live inside functions.

Public surface:

* ``THEME_DARK`` / ``THEME_LIGHT`` / ``THEME_MATERIAL`` — token
  identifiers used as session-state values.
* ``ALL_THEMES`` — ordered tuple for selectbox widgets.
* ``THEME_TOKENS`` — dict[theme_id, dict[token_name, value]] mirroring
  the prototype CSS variable table.
* ``build_os_css(theme: str) -> str`` — pure CSS builder. Tests
  inspect this without spinning up Streamlit.
* ``apply_os_theme(theme: str | None = None) -> None`` — injects CSS
  into the live Streamlit page.
* ``render_os_header(active_label, generated_at=None)`` — OS-style
  top tray (product mark + active module + system pills + timestamp).
* ``render_status_strip(badges)`` — secondary header strip.
* ``render_theme_selector(default)`` — sidebar widget; persists choice
  via ``st.session_state["finskillos_theme"]``.

The CSS targets Streamlit's own primitives (``.stApp``,
``section[data-testid="stSidebar"]``, ``div[data-testid="stMetric"]``,
``div[data-testid="stDataFrame"]`` …) so the theme applies even on
pages that have not been polished individually.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

# ---------------------------------------------------------------------------
# Theme identifiers
# ---------------------------------------------------------------------------

THEME_DARK = "dark"
THEME_LIGHT = "light"
THEME_MATERIAL = "material"

ALL_THEMES: tuple[str, ...] = (THEME_DARK, THEME_LIGHT, THEME_MATERIAL)

_THEME_LABELS: dict[str, str] = {
    THEME_DARK: "Dark OS",
    THEME_LIGHT: "Light OS",
    THEME_MATERIAL: "Material Reference",
}

SESSION_THEME_KEY = "finskillos_theme"


# ---------------------------------------------------------------------------
# Token tables (mirrored from prototypes/ui/os_style_mockup/index.html)
# ---------------------------------------------------------------------------


_DARK_TOKENS: dict[str, str] = {
    "bg": "#060910",
    "panel": "#0a0f16",
    "panel_2": "#0f1820",
    "panel_3": "#152030",
    "border": "#1a2d42",
    "border_strong": "#243d58",
    "text": "#e8f4ff",
    "muted": "#a8c8e8",
    "muted_2": "#6090b8",
    "cyan": "#00e5ff",
    "cyan_2": "#00b4cc",
    "amber": "#ffb800",
    "amber_2": "#e08000",
    "green": "#00ff88",
    "green_2": "#00cc66",
    "red": "#ff3b5c",
    "red_2": "#cc2040",
    "purple": "#a855f7",
    "scan_alpha": "0.18",
}

_LIGHT_TOKENS: dict[str, str] = {
    "bg": "#eef1f6",
    "panel": "#ffffff",
    "panel_2": "#f4f7fb",
    "panel_3": "#e9eef5",
    "border": "#cfd8e3",
    "border_strong": "#b4c1d1",
    "text": "#0a1828",
    "muted": "#2a3a52",
    "muted_2": "#4e6080",
    "cyan": "#0093a8",
    "cyan_2": "#006c7c",
    "amber": "#c47a00",
    "amber_2": "#9a5e00",
    "green": "#00964e",
    "green_2": "#006e3a",
    "red": "#d6294a",
    "red_2": "#a01a36",
    "purple": "#7826c8",
    "scan_alpha": "0.0",
}

_MATERIAL_TOKENS: dict[str, str] = {
    "bg": "#121212",
    "panel": "#1E1E1E",
    "panel_2": "#242526",
    "panel_3": "#2A2B2D",
    "border": "#3b3d3f",
    "border_strong": "#444746",
    "text": "#E3E3E3",
    "muted": "#C4C7C5",
    "muted_2": "#A2A5A4",
    "cyan": "#A8C7FA",
    "cyan_2": "#8AB4F8",
    "amber": "#FDE293",
    "amber_2": "#E0BC5E",
    "green": "#81C995",
    "green_2": "#6FAF81",
    "red": "#F2B8B5",
    "red_2": "#D68F8A",
    "purple": "#C58AF9",
    "scan_alpha": "0.0",
}

THEME_TOKENS: Mapping[str, Mapping[str, str]] = {
    THEME_DARK: _DARK_TOKENS,
    THEME_LIGHT: _LIGHT_TOKENS,
    THEME_MATERIAL: _MATERIAL_TOKENS,
}


# ---------------------------------------------------------------------------
# Tone vocabulary used by os_components
# ---------------------------------------------------------------------------

TONE_NEUTRAL = "neutral"
TONE_INFO = "info"
TONE_SUCCESS = "success"
TONE_WARNING = "warning"
TONE_DANGER = "danger"
TONE_CYAN = "cyan"
TONE_AMBER = "amber"
TONE_GREEN = "green"
TONE_RED = "red"
TONE_PURPLE = "purple"

ALL_TONES: tuple[str, ...] = (
    TONE_NEUTRAL,
    TONE_INFO,
    TONE_SUCCESS,
    TONE_WARNING,
    TONE_DANGER,
    TONE_CYAN,
    TONE_AMBER,
    TONE_GREEN,
    TONE_RED,
    TONE_PURPLE,
)

_TONE_TO_TOKEN: dict[str, str] = {
    TONE_NEUTRAL: "muted",
    TONE_INFO: "cyan",
    TONE_SUCCESS: "green",
    TONE_WARNING: "amber",
    TONE_DANGER: "red",
    TONE_CYAN: "cyan",
    TONE_AMBER: "amber",
    TONE_GREEN: "green",
    TONE_RED: "red",
    TONE_PURPLE: "purple",
}


def tone_to_token(tone: str) -> str:
    """Map a tone vocabulary string to the colour token name."""

    return _TONE_TO_TOKEN.get(tone, "muted")


# ---------------------------------------------------------------------------
# Pure CSS builder
# ---------------------------------------------------------------------------


def _resolve_theme(theme: str | None) -> str:
    if theme in THEME_TOKENS:
        return theme  # type: ignore[return-value]
    return THEME_DARK


def build_os_css(theme: str | None = None) -> str:
    """Return the full OS-theme CSS string for ``theme``.

    Pure function — no Streamlit dependency. Variables expose every
    token under the ``--fso-*`` namespace so test code can pattern-
    match them without re-deriving the palette.
    """

    theme_id = _resolve_theme(theme)
    tokens = THEME_TOKENS[theme_id]

    var_lines = "\n".join(
        f"  --fso-{key.replace('_', '-')}: {value};" for key, value in tokens.items()
    )

    text = tokens["text"]
    muted = tokens["muted"]
    muted_2 = tokens["muted_2"]
    bg = tokens["bg"]
    panel = tokens["panel"]
    panel_2 = tokens["panel_2"]
    panel_3 = tokens["panel_3"]
    border = tokens["border"]
    border_strong = tokens["border_strong"]
    cyan = tokens["cyan"]
    amber = tokens["amber"]
    green = tokens["green"]
    red = tokens["red"]
    scan_alpha = tokens["scan_alpha"]

    return f"""
<style id="fso-os-theme" data-theme="{theme_id}">
:root {{
{var_lines}
  --fso-font-mono: 'JetBrains Mono', 'Roboto Mono', 'Source Code Pro',
                    ui-monospace, SFMono-Regular, Menlo, monospace;
  --fso-font-head: 'Space Grotesk', 'Noto Sans KR', 'Inter',
                    system-ui, -apple-system, BlinkMacSystemFont,
                    'Segoe UI', sans-serif;
  --fso-glow-cyan:  0 0 22px rgba(0, 229, 255, 0.18);
  --fso-glow-amber: 0 0 22px rgba(255, 184, 0, 0.20);
  --fso-glow-red:   0 0 22px rgba(255, 59, 92, 0.22);
}}

/* App background + base font */
.stApp {{
  background: {bg};
  color: {text};
  font-family: var(--fso-font-mono);
}}
.stApp::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent 0px,
    transparent 2px,
    rgba(0, 229, 255, {scan_alpha}) 3px,
    transparent 4px
  );
  z-index: 0;
}}

/* Headings stay sans-serif */
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
  font-family: var(--fso-font-head);
  letter-spacing: 0.04em;
  color: {text};
}}
.stApp h2 {{ color: {cyan}; }}
.stApp h3 {{ color: {muted}; }}

/* Captions / muted text */
.stApp small, .stApp .stCaption, .stApp [data-testid="stCaption"] {{
  color: {muted_2} !important;
  letter-spacing: 0.04em;
}}

/* Sidebar */
section[data-testid="stSidebar"] > div {{
  background: linear-gradient(180deg, {panel}, {panel_2});
  border-right: 1px solid {border};
}}
section[data-testid="stSidebar"] * {{
  font-family: var(--fso-font-mono);
}}

/* Metric tiles */
div[data-testid="stMetric"] {{
  background: linear-gradient(135deg, {panel}, {panel_2});
  border: 1px solid {border};
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.02);
}}
div[data-testid="stMetricValue"] {{
  font-family: var(--fso-font-mono);
  color: {cyan};
  letter-spacing: 0.02em;
}}
div[data-testid="stMetricLabel"] {{
  color: {muted} !important;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-size: 11px;
}}

/* Dataframes / tables */
div[data-testid="stDataFrame"] {{
  border: 1px solid {border};
  border-radius: 8px;
  overflow: hidden;
  background: {panel};
}}

/* Buttons */
.stApp button[kind="primary"], .stApp button[kind="secondary"], .stApp .stButton > button {{
  font-family: var(--fso-font-mono);
  border: 1px solid {border_strong};
  background: {panel_2};
  color: {text};
  letter-spacing: 0.08em;
}}
.stApp .stButton > button:hover {{
  border-color: {cyan};
  color: {cyan};
  box-shadow: var(--fso-glow-cyan);
}}

/* Expander + alert containers */
.stApp [data-testid="stExpander"] {{
  border: 1px solid {border};
  border-radius: 6px;
  background: {panel_2};
}}
.stApp [data-testid="stAlert"] {{
  border: 1px solid {border};
  border-radius: 6px;
  background: {panel_2};
}}

/* Custom OS components ------------------------------------------------ */
.fso-tray {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  margin: -8px -8px 16px;
  background: linear-gradient(135deg, {panel}, {panel_3});
  border: 1px solid {border};
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.02);
}}
.fso-tray-mark {{
  font-family: var(--fso-font-head);
  font-weight: 700;
  font-size: 18px;
  color: {cyan};
  letter-spacing: 0.18em;
  text-shadow: var(--fso-glow-cyan);
}}
.fso-tray-meta {{
  font-size: 11px;
  color: {muted};
  letter-spacing: 0.25em;
  text-transform: uppercase;
}}
.fso-tray-active {{
  font-size: 12px;
  color: {amber};
  letter-spacing: 0.2em;
  text-transform: uppercase;
}}
.fso-pill {{
  display: inline-block;
  padding: 2px 10px;
  margin-left: 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}}
.fso-pill-cyan   {{ background: rgba(0,229,255,0.10); color: {cyan};   border: 1px solid {cyan}; }}
.fso-pill-amber  {{ background: rgba(255,184,0,0.10); color: {amber};  border: 1px solid {amber}; }}
.fso-pill-green  {{ background: rgba(0,255,136,0.10); color: {green};  border: 1px solid {green}; }}
.fso-pill-red    {{ background: rgba(255,59,92,0.10); color: {red};    border: 1px solid {red}; }}
.fso-pill-muted  {{
  background: rgba(255,255,255,0.04);
  color: {muted_2};
  border: 1px solid {border};
}}

.fso-panel {{
  background: linear-gradient(135deg, {panel}, {panel_2});
  border: 1px solid {border};
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 10px;
}}
.fso-panel-title {{
  font-family: var(--fso-font-head);
  font-size: 14px;
  color: {text};
  letter-spacing: 0.12em;
  text-transform: uppercase;
}}
.fso-panel-subtitle {{
  font-size: 11px;
  color: {muted};
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin-top: 2px;
}}

.fso-section-eyebrow {{
  font-size: 10px;
  color: {muted_2};
  letter-spacing: 0.32em;
  text-transform: uppercase;
  margin-bottom: 2px;
}}
.fso-section-title {{
  font-family: var(--fso-font-head);
  font-size: 18px;
  color: {text};
  letter-spacing: 0.05em;
}}

.fso-empty {{
  border: 1px dashed {border};
  border-radius: 8px;
  background: {panel_2};
  padding: 16px 18px;
  margin: 6px 0 14px;
}}
.fso-empty-title {{
  font-family: var(--fso-font-head);
  color: {amber};
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 12px;
  margin-bottom: 6px;
}}
.fso-empty-msg {{ color: {muted}; font-size: 13px; line-height: 1.5; }}
</style>
""".strip()


# ---------------------------------------------------------------------------
# Streamlit-bound helpers (lazy import)
# ---------------------------------------------------------------------------


def get_active_theme() -> str:
    """Return the currently-selected theme id (default DARK)."""

    import streamlit as st

    value = st.session_state.get(SESSION_THEME_KEY, THEME_DARK)
    if value not in THEME_TOKENS:
        return THEME_DARK
    return value


def apply_os_theme(theme: str | None = None) -> None:
    """Inject the OS theme CSS into the current Streamlit page.

    Reads ``st.session_state[SESSION_THEME_KEY]`` when ``theme`` is
    not provided. Safe to call once per ``run_app`` invocation —
    Streamlit deduplicates ``markdown(unsafe_allow_html=True)`` blocks
    by their inline ``id`` attribute (``id="fso-os-theme"``).
    """

    import streamlit as st

    resolved = _resolve_theme(theme or st.session_state.get(SESSION_THEME_KEY))
    st.markdown(build_os_css(resolved), unsafe_allow_html=True)


def render_theme_selector(*, default: str = THEME_DARK) -> str:
    """Render the sidebar theme selectbox and return the chosen id.

    Persists the choice on ``st.session_state[SESSION_THEME_KEY]`` so
    subsequent calls to ``apply_os_theme()`` pick it up without
    re-querying the widget.
    """

    import streamlit as st

    current = st.session_state.get(SESSION_THEME_KEY, default)
    if current not in THEME_TOKENS:
        current = default

    labels = [_THEME_LABELS[tid] for tid in ALL_THEMES]
    index = ALL_THEMES.index(current)
    selected_label = st.selectbox(
        "Theme",
        labels,
        index=index,
        key="finskillos_theme_selector",
        help="OS 비주얼 테마. Dark / Light / Material 중에서 선택합니다.",
    )
    selected_id = ALL_THEMES[labels.index(selected_label)]
    st.session_state[SESSION_THEME_KEY] = selected_id
    return selected_id


def render_os_header(
    active_label: str | None = None,
    *,
    generated_at: datetime | None = None,
) -> None:
    """Render the OS-style top tray.

    Includes the product mark, the active module label (capitalised),
    a small "READ-MODE" pill so the user always knows the app does
    not auto-execute, and the generation timestamp.
    """

    import streamlit as st

    now = generated_at or datetime.utcnow()
    active = (active_label or "—").upper()
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    st.markdown(
        f"""
        <div class="fso-tray">
            <div>
                <div class="fso-tray-mark">FINSKILLOS v2.1</div>
                <div class="fso-tray-meta">
                    interpretation-first · descriptive-only
                </div>
            </div>
            <div style="text-align:right;">
                <div class="fso-tray-active">
                    MODULE · {active}
                    <span class="fso-pill fso-pill-cyan">READ-MODE</span>
                    <span class="fso-pill fso-pill-muted">LOCAL DB</span>
                </div>
                <div class="fso-tray-meta" style="margin-top:6px;">
                    {timestamp}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_strip(badges: Sequence[tuple[str, str]]) -> None:
    """Render a secondary header strip of (label, tone) badges.

    ``tone`` is mapped via :func:`tone_to_token` to the OS palette
    token name. Unknown tones fall back to the muted pill.
    """

    if not badges:
        return

    import streamlit as st

    pill_html = []
    accent_tokens = {"cyan", "amber", "green", "red"}
    for label, tone in badges:
        token = tone_to_token(tone)
        variant = token if token in accent_tokens else "muted"
        pill_html.append(
            f'<span class="fso-pill fso-pill-{variant}">{label}</span>'
        )
    st.markdown(
        '<div style="margin-bottom:10px;">' + " ".join(pill_html) + "</div>",
        unsafe_allow_html=True,
    )


__all__ = [
    "ALL_THEMES",
    "ALL_TONES",
    "SESSION_THEME_KEY",
    "THEME_DARK",
    "THEME_LIGHT",
    "THEME_MATERIAL",
    "THEME_TOKENS",
    "TONE_AMBER",
    "TONE_CYAN",
    "TONE_DANGER",
    "TONE_GREEN",
    "TONE_INFO",
    "TONE_NEUTRAL",
    "TONE_PURPLE",
    "TONE_RED",
    "TONE_SUCCESS",
    "TONE_WARNING",
    "apply_os_theme",
    "build_os_css",
    "get_active_theme",
    "render_os_header",
    "render_status_strip",
    "render_theme_selector",
    "tone_to_token",
]
