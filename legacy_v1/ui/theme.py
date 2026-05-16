"""Design tokens and theme helpers for FinSkillOS."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


PLOTLY_COLORS = [
    "#25f2c7",
    "#38a3ff",
    "#f4b740",
    "#a874ff",
    "#ff5b73",
    "#6ef3ff",
    "#7bd88f",
]


LIGHT_APPLIED_RULES_CSS = '\n        /* FINSKILLOS_APPLIED_RULES_THEME_V11_3_LIGHT\n           Explicit Applied Rules light theme override.\n           This is injected from apply_dashboard_style(theme) when theme == Light.\n           It intentionally uses stronger specificity than the v11 custom CSS.\n        */\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip > div {\n            border: 1px solid rgba(15, 23, 42, 0.10) !important;\n            background:\n                radial-gradient(circle at 0% 0%, rgba(20, 184, 166, 0.08), transparent 10rem),\n                linear-gradient(180deg, #ffffff, #f8fafc) !important;\n            color: #0f172a !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.92),\n                0 8px 20px rgba(15, 23, 42, 0.06) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade-label,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip small {\n            color: #64748b !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade-value,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip span {\n            color: #0fbea9 !important;\n            text-shadow: none !important;\n        }\n'

DARK_APPLIED_RULES_CSS = '\n        /* FINSKILLOS_APPLIED_RULES_THEME_V11_3_DARK\n           Explicit Applied Rules dark theme override.\n        */\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip > div {\n            border: 1px solid var(--fs-line) !important;\n            background:\n                radial-gradient(circle at 0% 0%, rgba(0, 212, 160, 0.10), transparent 10rem),\n                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98)) !important;\n            color: var(--fs-ink) !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.04),\n                0 8px 20px rgba(0, 0, 0, 0.12) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade-label,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip small {\n            color: var(--fs-muted) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-governance-grade-value,\n        html body [data-testid="stAppViewContainer"] .fs-rule-health-strip span {\n            color: var(--fs-teal) !important;\n            text-shadow: none !important;\n        }\n'

LIGHT_OVERVIEW_FOOTER_CSS = '\n        /* FINSKILLOS_OVERVIEW_FOOTER_THEME_V9_6_LIGHT\n           Explicit light-theme override for Overview footer stat cards.\n           The v9.x footer stat cards used hard-coded dark gradients, so they\n           stayed dark even when the rest of the dashboard used the Light theme.\n        */\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card {\n            border: 1px solid rgba(15, 23, 42, 0.10) !important;\n            background:\n                radial-gradient(circle at 0% 0%, rgba(20, 184, 166, 0.08), transparent 10rem),\n                linear-gradient(180deg, #ffffff, #f8fafc) !important;\n            color: #0f172a !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.92),\n                0 8px 20px rgba(15, 23, 42, 0.06) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-kicker,\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-caption {\n            color: #64748b !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-value {\n            color: #0f172a !important;\n            text-shadow: none !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="teal"] .fs-overview-stat-value {\n            color: #0fbea9 !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="blue"] .fs-overview-stat-value {\n            color: #2563eb !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="purple"] .fs-overview-stat-value {\n            color: #8b5cf6 !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button {\n            box-shadow:\n                0 14px 30px rgba(37, 99, 235, 0.16),\n                inset 0 1px 0 rgba(255, 255, 255, 0.20) !important;\n        }\n'

DARK_OVERVIEW_FOOTER_CSS = '\n        /* FINSKILLOS_OVERVIEW_FOOTER_THEME_V9_6_DARK\n           Explicit dark-theme override for Overview footer stat cards.\n        */\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card {\n            border: 1px solid rgba(129, 166, 202, 0.16) !important;\n            background:\n                radial-gradient(circle at 0% 0%, rgba(25, 198, 180, 0.10), transparent 11rem),\n                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98)) !important;\n            color: var(--fs-ink) !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.04),\n                0 8px 20px rgba(0, 0, 0, 0.12) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-kicker,\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-caption {\n            color: var(--fs-muted) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-value {\n            color: var(--fs-ink) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="teal"] .fs-overview-stat-value {\n            color: var(--fs-teal) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="blue"] .fs-overview-stat-value {\n            color: var(--fs-blue) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] .fs-overview-stat-card[data-tone="purple"] .fs-overview-stat-value {\n            color: var(--fs-purple) !important;\n        }\n'

LIGHT_CSV_UPLOAD_CSS = '\n        /* FINSKILLOS_CSV_UPLOAD_THEME_V13_LIGHT\n           Explicit light-theme styling for Streamlit file uploader.\n           Streamlit\'s uploader internals can keep dark filename/dropzone\n           surfaces even when the surrounding dashboard is light.\n        */\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] {\n            color: #0f172a !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {\n            border: 1px solid rgba(15, 23, 42, 0.14) !important;\n            background:\n                linear-gradient(180deg, #ffffff, #f8fafc) !important;\n            color: #0f172a !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.90),\n                0 6px 16px rgba(15, 23, 42, 0.04) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section:hover,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"]:hover {\n            border-color: rgba(20, 184, 166, 0.46) !important;\n            background:\n                linear-gradient(180deg, #ffffff, #f1f5f9) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] small,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] span,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] p,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] div {\n            color: #334155 !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [role="button"] {\n            border: 1px solid rgba(15, 23, 42, 0.14) !important;\n            background:\n                linear-gradient(180deg, #ffffff, #eef2f7) !important;\n            color: #0f172a !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.80),\n                0 4px 10px rgba(15, 23, 42, 0.05) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button:hover,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [role="button"]:hover {\n            border-color: rgba(20, 184, 166, 0.52) !important;\n            background:\n                linear-gradient(180deg, #f8fafc, #e2e8f0) !important;\n            color: #0f172a !important;\n        }\n\n        /* Uploaded filename row/pill. Streamlit versions differ, so target\n           common uploader descendants after the input/dropzone generically. */\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] ul,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] li,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid*="file"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="uploaded"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="File"] {\n            background-color: transparent !important;\n            color: #0f172a !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid*="stFileUploaderFile"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid*="UploadedFile"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="fileName"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="file-name"] {\n            border: 1px solid rgba(15, 23, 42, 0.12) !important;\n            border-radius: 10px !important;\n            background:\n                linear-gradient(180deg, #ffffff, #f8fafc) !important;\n            color: #0f172a !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] svg {\n            color: #64748b !important;\n            fill: currentColor !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [aria-label*="Delete"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [aria-label*="Remove"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button[title*="Delete"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button[title*="Remove"] {\n            background: transparent !important;\n            color: #64748b !important;\n            border-color: transparent !important;\n            box-shadow: none !important;\n        }\n'

DARK_CSV_UPLOAD_CSS = '\n        /* FINSKILLOS_CSV_UPLOAD_THEME_V13_DARK\n           Explicit dark-theme styling for Streamlit file uploader.\n        */\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] {\n            color: var(--fs-ink) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {\n            border: 1px solid var(--fs-line) !important;\n            background:\n                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98)) !important;\n            color: var(--fs-ink) !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.04),\n                0 8px 18px rgba(0, 0, 0, 0.12) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] section:hover,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"]:hover {\n            border-color: rgba(25, 198, 180, 0.52) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] small,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] span,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] p,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] div {\n            color: var(--fs-soft) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [role="button"] {\n            border: 1px solid var(--fs-line) !important;\n            background:\n                linear-gradient(180deg, rgba(17, 34, 54, 0.98), rgba(9, 20, 35, 0.98)) !important;\n            color: var(--fs-ink) !important;\n            box-shadow:\n                inset 0 1px 0 rgba(255, 255, 255, 0.04),\n                0 6px 14px rgba(0, 0, 0, 0.14) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] button:hover,\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [role="button"]:hover {\n            border-color: rgba(25, 198, 180, 0.52) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid*="stFileUploaderFile"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [data-testid*="UploadedFile"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="fileName"],\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] [class*="file-name"] {\n            border: 1px solid var(--fs-line) !important;\n            border-radius: 10px !important;\n            background:\n                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98)) !important;\n            color: var(--fs-ink) !important;\n        }\n\n        html body [data-testid="stAppViewContainer"] [data-testid="stFileUploader"] svg {\n            color: var(--fs-muted) !important;\n            fill: currentColor !important;\n        }\n'

def apply_dashboard_style(theme: str = "Dark") -> None:
    """Apply the FinSkillOS product shell theme."""


    # Streamlit file_uploader needs explicit theme-aware CSS because its
    # internal filename/dropzone/button elements can keep dark surfaces under
    # the Light theme.
    fs_upload_theme_name = str(theme or "Dark").strip().lower()
    fs_csv_upload_theme_css = LIGHT_CSV_UPLOAD_CSS if fs_upload_theme_name.startswith("light") else DARK_CSV_UPLOAD_CSS
    st.markdown(f"<style>{fs_csv_upload_theme_css}</style>", unsafe_allow_html=True)


    # Overview footer stat cards need explicit theme-aware CSS because v9.x
    # styles used hard-coded dark surfaces. Existing CSS variables may still
    # resolve to dark values under Streamlit's Light theme.
    fs_overview_theme_name = str(theme or "Dark").strip().lower()
    fs_overview_footer_theme_css = LIGHT_OVERVIEW_FOOTER_CSS if fs_overview_theme_name.startswith("light") else DARK_OVERVIEW_FOOTER_CSS
    st.markdown(f"<style>{fs_overview_footer_theme_css}</style>", unsafe_allow_html=True)


    # Applied Rules custom widgets need explicit theme-aware CSS because
    # their original v11 styles used hard-coded dark surfaces, while existing
    # CSS variables may also remain dark under Streamlit's Light theme.
    fs_theme_name = str(theme or "Dark").strip().lower()
    fs_applied_rules_theme_css = LIGHT_APPLIED_RULES_CSS if fs_theme_name.startswith("light") else DARK_APPLIED_RULES_CSS
    st.markdown(f"<style>{fs_applied_rules_theme_css}</style>", unsafe_allow_html=True)

    st.markdown(
        """
        <style>
        @import url("https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap");

        *, *::before, *::after {
            box-sizing: border-box;
        }

        :root {
            --fs-font-sans: "DM Sans", "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", "NanumGothic", "Aptos", "Segoe UI", sans-serif;
            --fs-bg: #0b0f19;
            --fs-bg-soft: #111827;
            --fs-sidebar: #111827;
            --fs-panel: rgba(21, 30, 45, 0.92);
            --fs-panel-strong: rgba(26, 37, 64, 0.96);
            --fs-panel-hover: rgba(31, 45, 69, 0.98);
            --fs-card-bg: linear-gradient(180deg, rgba(14, 32, 52, 0.92), rgba(7, 17, 31, 0.94));
            --fs-panel-card-bg: linear-gradient(180deg, rgba(12, 27, 45, 0.9), rgba(7, 17, 31, 0.95));
            --fs-control-bg: linear-gradient(180deg, rgba(12, 26, 43, 0.78), rgba(7, 17, 31, 0.86));
            --fs-table-bg: rgba(6, 16, 30, 0.72);
            --fs-table-header-bg: rgba(129, 166, 202, 0.08);
            --fs-line: rgba(255, 255, 255, 0.08);
            --fs-line-strong: rgba(0, 212, 160, 0.44);
            --fs-ink: #e8edf5;
            --fs-muted: #7a8ba0;
            --fs-soft: #b8c4d4;
            --fs-teal: #00d4a0;
            --fs-cyan: #35d6ff;
            --fs-blue: #4f91e8;
            --fs-red: #f05151;
            --fs-amber: #f5a623;
            --fs-purple: #a874ff;
            --fs-green: #35d990;
            --fs-accent-strong: #19c6b4;
            --fs-accent-deep: #127c8c;
            --fs-accent-soft: rgba(25, 198, 180, 0.12);
            --fs-accent-line: rgba(25, 198, 180, 0.32);
            --fs-button-bg: linear-gradient(135deg, #169c9f 0%, #1a86ae 52%, #246db9 100%);
            --fs-button-hover-bg: linear-gradient(135deg, #1bb0aa 0%, #1f95bd 52%, #2b77c6 100%);
            --fs-button-shadow: 0 10px 24px rgba(17, 123, 140, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.14);
            --fs-button-shadow-hover: 0 14px 28px rgba(17, 123, 140, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.18);
            --fs-surface-tint: linear-gradient(180deg, rgba(18, 42, 60, 0.9), rgba(8, 20, 34, 0.94));
            --fs-radius: 8px;
            --fs-shadow: 0 10px 34px rgba(0, 0, 0, 0.28);
            --fs-glow: 0 0 0 1px rgba(0, 212, 160, 0.3), 0 0 22px rgba(0, 212, 160, 0.09);
            --fs-ease: cubic-bezier(0.22, 1, 0.36, 1);
            --fs-fast: 140ms;
            --fs-medium: 240ms;
            --fs-sidebar-width: 208px;
            --fs-sidebar-pad-x: 12px;
            --fs-gap-xs: 4px;
            --fs-gap-sm: 8px;
            --fs-gap-md: 14px;
            --fs-gap-lg: 18px;
            --fs-gap-xl: 24px;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 18% 0%, rgba(0, 212, 160, 0.08), transparent 25rem),
                radial-gradient(circle at 92% 20%, rgba(79, 145, 232, 0.1), transparent 24rem),
                linear-gradient(135deg, #0b0f19 0%, #08111f 52%, #0b0f19 100%) !important;
            color: var(--fs-ink);
            font-family: var(--fs-font-sans);
        }

        [data-testid="stHeader"] {
            height: 0;
            background: transparent;
            border-bottom: 0;
            backdrop-filter: none;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        [data-testid="stAppViewContainer"] {
            display: flex;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(17, 24, 39, 0.98), rgba(11, 15, 25, 0.98)),
                var(--fs-sidebar);
            border-right: 1px solid var(--fs-line);
            width: var(--fs-sidebar-width) !important;
            min-width: var(--fs-sidebar-width) !important;
            max-width: var(--fs-sidebar-width) !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            width: var(--fs-sidebar-width);
            padding: 20px 0 16px 0;
            overflow-x: hidden;
        }
        [data-testid="stSidebarContent"] {
            width: var(--fs-sidebar-width) !important;
            padding: 20px 0 16px 0 !important;
            overflow-x: hidden;
        }
        [data-testid="stSidebarUserContent"] {
            padding-left: 6px !important;
            padding-right: 6px !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
            color: var(--fs-soft);
        }

        [data-testid="stMain"],
        section.main {
            min-width: 0;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        [data-testid="stMainBlockContainer"],
        .main .block-container,
        section.main > div.block-container {
            padding: 18px 20px 28px 20px !important;
            max-width: none;
            width: 100%;
            animation: fs-page-in var(--fs-medium) var(--fs-ease) both;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
        .main .block-container [data-testid="stVerticalBlock"] {
            gap: var(--fs-gap-md);
        }
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"],
        .main .block-container [data-testid="stHorizontalBlock"] {
            gap: var(--fs-gap-md);
            margin: 0;
            align-items: stretch;
        }
        [data-testid="column"] > [data-testid="stVerticalBlock"] {
            gap: var(--fs-gap-sm);
            height: 100%;
        }
        [data-testid="column"] {
            display: flex;
        }
        [data-testid="column"] > div {
            width: 100%;
        }
        [data-testid="stMainBlockContainer"] div[data-testid="stElementContainer"],
        .main .block-container div[data-testid="stElementContainer"] {
            margin: 0;
        }

        h1, h2, h3, h4 {
            color: var(--fs-ink);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            padding: 0.72rem 0.82rem;
            background: linear-gradient(180deg, rgba(21, 30, 45, 0.92), rgba(13, 21, 35, 0.94));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--fs-muted);
            font-size: 0.68rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--fs-teal);
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            border-radius: var(--fs-radius);
            overflow: auto;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--fs-line);
            background: rgba(11, 18, 31, 0.72);
            max-width: 100%;
        }
        div[data-testid="stMarkdownContainer"] h3 {
            margin: 0 0 var(--fs-gap-xs) 0;
            line-height: 1.12;
            font-size: 1.38rem;
        }
        div[data-testid="stMarkdownContainer"] h4 {
            margin: 0 0 2px 0;
            line-height: 1.14;
            font-size: 1rem;
        }
        div[data-testid="stMarkdownContainer"] h5 {
            margin: var(--fs-gap-sm) 0 var(--fs-gap-xs) 0;
            line-height: 1.12;
            font-size: 0.86rem;
        }
        div[data-testid="stMarkdownContainer"] p {
            margin: 0;
        }
        div[data-testid="stPlotlyChart"] {
            min-height: 235px;
            background: transparent !important;
            border: 0 !important;
        }
        div[data-testid="stPlotlyChart"] .modebar {
            display: none !important;
        }
        div[data-testid="stPlotlyChart"] .js-plotly-plot,
        div[data-testid="stPlotlyChart"] .plot-container,
        div[data-testid="stPlotlyChart"] .svg-container {
            background: transparent !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stPopover"] > button,
        [data-testid="stPopover"] button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.38rem;
            border-radius: 12px;
            border: 1px solid var(--fs-accent-line);
            background: var(--fs-button-bg);
            color: #f3fffd;
            font-weight: 700;
            min-height: 2.25rem;
            padding: 0.45rem 0.72rem;
            font-size: 0.78rem;
            line-height: 1;
            text-align: center;
            letter-spacing: -0.01em;
            box-shadow: var(--fs-button-shadow);
            transition: transform var(--fs-fast) var(--fs-ease), border-color var(--fs-fast) var(--fs-ease), box-shadow var(--fs-fast) var(--fs-ease), filter var(--fs-fast) var(--fs-ease), background var(--fs-fast) var(--fs-ease);
        }

        .stButton > button p,
        .stDownloadButton > button p,
        [data-testid="stPopover"] button p {
            width: 100%;
            margin: 0 !important;
            color: inherit !important;
            font: inherit !important;
            line-height: 1.05 !important;
            text-align: center;
            white-space: normal;
            overflow-wrap: anywhere;
        }

        .fs-control-shell [data-testid="stPopover"] > button,
        .fs-control-shell [data-testid="stPopover"] button {
            width: 2.25rem !important;
            min-width: 2.25rem !important;
            max-width: 2.25rem !important;
            height: 2.25rem !important;
            min-height: 2.25rem !important;
            padding: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid rgba(129, 166, 202, 0.18) !important;
            border-radius: 999px !important;
            background: linear-gradient(180deg, rgba(21, 37, 56, 0.92), rgba(12, 23, 39, 0.94)) !important;
            color: var(--fs-ink) !important;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 4px 12px rgba(0, 0, 0, 0.18) !important;
        }

        .fs-control-shell [data-testid="stPopover"] svg,
        .fs-control-shell [data-testid="stPopover"] [data-testid="stIconMaterial"] {
            display: none !important;
        }

        .fs-control-shell [data-testid="stPopover"] > button p,
        .fs-control-shell [data-testid="stPopover"] button p {
            color: inherit !important;
            font-family: var(--fs-font-sans) !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            height: 100% !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stPopover"] > button:hover {
            border-color: rgba(118, 235, 219, 0.52);
            background: var(--fs-button-hover-bg);
            box-shadow: var(--fs-button-shadow-hover);
            transform: translateY(-1px);
            filter: saturate(1.04);
        }

        .fs-control-shell [data-testid="stPopover"] > button:hover,
        .fs-control-shell [data-testid="stPopover"] button:hover,
        .fs-control-shell [data-testid="stPopover"] > button:focus,
        .fs-control-shell [data-testid="stPopover"] button:focus,
        .fs-control-shell [data-testid="stPopover"] > button:active,
        .fs-control-shell [data-testid="stPopover"] button:active,
        .fs-control-shell [data-testid="stPopover"] > button[aria-expanded="true"],
        .fs-control-shell [data-testid="stPopover"] button[aria-expanded="true"] {
            border-color: var(--fs-accent-line) !important;
            background: linear-gradient(180deg, rgba(24, 43, 64, 0.96), rgba(14, 28, 47, 0.98)) !important;
            color: var(--fs-ink) !important;
            box-shadow: 0 0 0 1px rgba(25, 198, 180, 0.16), 0 8px 18px rgba(14, 87, 102, 0.18) !important;
        }

        [data-baseweb="popover"] {
            font-family: var(--fs-font-sans) !important;
        }
        [data-baseweb="popover"]:has(.fs-sample-help) {
            background: var(--fs-panel-card-bg) !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 12px !important;
            box-shadow: var(--fs-shadow) !important;
        }
        [data-baseweb="popover"]:has(.fs-sample-help) > div {
            background: transparent !important;
            border: 0 !important;
            border-radius: inherit !important;
            box-shadow: none !important;
            color: var(--fs-ink) !important;
        }
        [data-baseweb="popover"]:not(:has(.fs-sample-help)) > div {
            background: var(--fs-panel-card-bg) !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 12px !important;
            box-shadow: var(--fs-shadow) !important;
            color: var(--fs-ink) !important;
        }
        [data-baseweb="popover"] [data-testid="stMarkdownContainer"],
        [data-baseweb="popover"] p {
            color: var(--fs-soft) !important;
            font-family: var(--fs-font-sans) !important;
            line-height: 1.55;
        }
        .fs-sample-help {
            max-width: 28rem;
            font-family: var(--fs-font-sans);
        }
        .fs-sample-help-title {
            color: var(--fs-ink);
            font-size: 0.92rem;
            font-weight: 800;
            margin-bottom: 0.42rem;
        }
        .fs-sample-help-body {
            color: var(--fs-soft);
            font-size: 0.82rem;
            line-height: 1.55;
        }

        .stButton > button:disabled,
        .stDownloadButton > button:disabled {
            opacity: 0.48;
            transform: none;
            box-shadow: none;
            cursor: not-allowed;
        }

        .stButton > button:focus-visible,
        .stDownloadButton > button:focus-visible,
        button:focus-visible,
        input:focus-visible,
        [role="button"]:focus-visible {
            outline: 2px solid var(--fs-teal) !important;
            outline-offset: 2px;
        }

        [data-baseweb="select"] > div,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        [data-testid="stFileUploader"] section {
            background: rgba(7, 17, 31, 0.95);
            border-color: var(--fs-line);
            border-radius: var(--fs-radius);
            color: var(--fs-ink);
            min-height: 2.42rem;
            transition: border-color var(--fs-fast) var(--fs-ease), box-shadow var(--fs-fast) var(--fs-ease);
        }
        [data-testid="stWidgetLabel"] {
            min-height: 1rem;
            margin-bottom: var(--fs-gap-xs);
        }
        [data-testid="stWidgetLabel"] p {
            color: var(--fs-muted);
            font-size: 0.66rem;
            font-weight: 760;
            line-height: 1;
            letter-spacing: 0.01em;
            white-space: nowrap;
        }
        [data-baseweb="select"] > div:hover,
        [data-testid="stTextInput"] input:hover,
        [data-testid="stTextArea"] textarea:hover,
        [data-testid="stNumberInput"] input:hover,
        [data-testid="stFileUploader"] section:hover {
            border-color: rgba(37, 242, 199, 0.36);
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stNumberInput"] input:focus {
            border-color: rgba(37, 242, 199, 0.48) !important;
            box-shadow: 0 0 0 1px rgba(37, 242, 199, 0.18);
        }
        [data-testid="stNumberInputContainer"] {
            border-radius: var(--fs-radius) !important;
            overflow: hidden !important;
        }
        [data-testid="stNumberInputContainer"] > div:last-child {
            background: rgba(7, 17, 31, 0.95) !important;
            background-color: rgba(7, 17, 31, 0.95) !important;
            border: 1px solid var(--fs-line) !important;
            border-left: 0 !important;
            border-radius: 0 var(--fs-radius) var(--fs-radius) 0 !important;
        }
        [data-testid="stNumberInput"] button {
            background: rgba(7, 17, 31, 0.95) !important;
            background-color: rgba(7, 17, 31, 0.95) !important;
            border-color: var(--fs-line) !important;
            color: var(--fs-soft) !important;
            min-height: 2.42rem !important;
            transition: border-color var(--fs-fast) var(--fs-ease), color var(--fs-fast) var(--fs-ease);
        }
        [data-testid="stNumberInputStepDown"],
        [data-testid="stNumberInputStepUp"] {
            background: transparent !important;
            background-color: transparent !important;
            border: 0 !important;
            border-left: 1px solid var(--fs-line) !important;
            border-radius: 0 !important;
            color: var(--fs-soft) !important;
        }
        [data-testid="stNumberInput"] button:hover {
            border-color: rgba(37, 242, 199, 0.36) !important;
            color: var(--fs-ink) !important;
        }
        [data-testid="stNumberInput"] button svg {
            color: currentColor !important;
            fill: currentColor !important;
        }
        [data-testid="stFileUploader"] {
            min-width: 0;
            min-height: 2.42rem;
            position: relative;
        }
        [data-testid="stFileUploader"] section {
            min-height: 2.42rem;
            max-height: 2.42rem;
            padding: 0.34rem 0.58rem;
            display: flex;
            align-items: center;
            overflow: hidden;
        }
        [data-testid="stFileUploader"] section > div {
            min-width: 0;
            width: 100%;
            gap: 0.42rem;
            align-items: center;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {
            min-width: 0;
            flex: 1 1 auto;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] > div {
            display: none;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
            content: "Drop or browse CSV";
            display: block;
            color: var(--fs-soft);
            font-size: 0.72rem;
            font-weight: 760;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) [data-testid="stFileUploaderDropzoneInstructions"]::before {
            content: "";
        }
        [data-testid="stFileUploader"] section button {
            min-height: 1.62rem;
            padding: 0.18rem 0.58rem;
            border-radius: var(--fs-radius);
            border-color: rgba(129, 166, 202, 0.22);
            background: rgba(21, 30, 45, 0.72);
            color: var(--fs-soft);
            font-size: 0.72rem;
            font-weight: 720;
        }
        [data-testid="stFileUploader"] input[type="file"] {
            width: 0.1px;
            height: 0.1px;
            opacity: 0;
            overflow: hidden;
            position: absolute;
            z-index: -1;
        }
        [data-testid="stFileUploader"] small {
            display: none;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
            display: flex !important;
            align-items: center !important;
            gap: 0.28rem !important;
            position: absolute !important;
            left: 0.22rem;
            right: 0.22rem;
            top: 50%;
            transform: translateY(-50%);
            z-index: 2;
            max-width: 100%;
            min-height: 1.55rem !important;
            height: 1.72rem !important;
            margin-top: 0 !important;
            padding: 0.16rem 0.28rem !important;
            border: 0 !important;
            border-radius: 8px !important;
            background: rgba(7, 17, 31, 0.96) !important;
            color: var(--fs-soft) !important;
            font-size: 0.62rem !important;
            line-height: 1 !important;
            overflow: hidden;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div:first-child {
            display: none !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div {
            min-width: 0 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
            max-width: 100% !important;
            color: var(--fs-soft) !important;
            font-size: 0.62rem !important;
            font-weight: 650 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button {
            width: 0.88rem !important;
            height: 0.88rem !important;
            min-width: 0.88rem !important;
            min-height: 0.88rem !important;
            padding: 0 !important;
            border: 1px solid rgba(129, 166, 202, 0.22) !important;
            background: rgba(7, 17, 31, 0.7) !important;
            color: var(--fs-soft) !important;
        }
        [data-testid="stCaptionContainer"] p {
            color: var(--fs-muted);
            font-size: 0.66rem;
            line-height: 1.18;
            margin: 0 0 var(--fs-gap-sm) 0;
        }

        .fs-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 var(--fs-sidebar-pad-x) 16px var(--fs-sidebar-pad-x);
            padding: 0 0 20px 0;
            border-bottom: 1px solid var(--fs-line);
            min-width: 0;
        }

        .fs-logo-mark {
            width: 32px;
            height: 32px;
            display: grid;
            place-items: center;
            border-radius: 8px;
            color: white;
            font-weight: 900;
            font-size: 0.82rem;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #00d4a0 0%, #0099ff 50%, #5e4dff 100%);
            box-shadow: 
                0 2px 8px rgba(0, 212, 160, 0.25),
                0 0 0 1px rgba(255,255,255,0.15) inset,
                0 4px 12px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* 빛 반사 효과 */
        .fs-logo-mark::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 60%;
            height: 60%;
            background: linear-gradient(
                135deg,
                rgba(255,255,255,0.35) 0%,
                rgba(255,255,255,0) 60%
            );
            border-radius: 50%;
            pointer-events: none;
        }

        /* 미세한 inner glow */
        .fs-logo-mark::after {
            content: '';
            position: absolute;
            inset: 1px;
            border-radius: 7px;
            background: linear-gradient(
                180deg,
                rgba(255,255,255,0.12),
                rgba(255,255,255,0)
            );
            pointer-events: none;
        }

        /* Hover 효과 */
        .fs-brand:hover .fs-logo-mark {
            transform: translateY(-1px) scale(1.05);
            box-shadow: 
                0 4px 16px rgba(0, 212, 160, 0.35),
                0 0 0 1px rgba(255,255,255,0.2) inset;
        }
        .fs-brand-title {
            color: var(--fs-ink);
            font-size: 0.94rem;
            font-weight: 830;
            line-height: 1;
            white-space: nowrap;
        }
        .fs-brand-title span {
            color: var(--fs-blue);
        }
        .fs-brand-subtitle {
            color: var(--fs-muted);
            font-size: 0.58rem;
            margin-top: 0.18rem;
            white-space: nowrap;
        }
        .fs-nav-label {
            color: var(--fs-muted);
            font-size: 0.6rem;
            font-weight: 760;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 var(--fs-sidebar-pad-x) 6px var(--fs-sidebar-pad-x);
        }

        .fs-nav-item {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.78rem 0.82rem;
            margin: 0.22rem 0;
            border: 1px solid transparent;
            border-radius: var(--fs-radius);
            color: var(--fs-soft);
            background: transparent;
        }
        .fs-nav-item-active {
            color: var(--fs-teal);
            border-color: rgba(37, 242, 199, 0.42);
            background: linear-gradient(90deg, rgba(37, 242, 199, 0.15), rgba(56, 163, 255, 0.06));
            box-shadow: inset 3px 0 0 var(--fs-teal);
        }
        [data-testid="stSidebar"] [role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0;
            margin-bottom: 12px;
            width: 100%;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border: 1px solid transparent;
            border-left: 2px solid transparent;
            border-radius: 0;
            padding: 10px var(--fs-sidebar-pad-x);
            margin: 0;
            background: transparent;
            width: 100%;
            min-height: 38px;
            transition: border-color var(--fs-fast) var(--fs-ease), background var(--fs-fast) var(--fs-ease), color var(--fs-fast) var(--fs-ease), transform var(--fs-fast) var(--fs-ease);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
            display: none;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label p {
            color: inherit;
            font-size: 0.78rem;
            font-weight: 650;
            line-height: 1.25;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: transparent;
            border-left-color: rgba(37, 242, 199, 0.32);
            background: rgba(37, 242, 199, 0.06);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            border-color: transparent;
            border-left-color: var(--fs-teal);
            background: rgba(37, 242, 199, 0.12);
            box-shadow: none;
            color: var(--fs-teal);
            animation: fs-nav-lock var(--fs-medium) var(--fs-ease) both;
        }
        .fs-nav-icon {
            width: 1rem;
            color: inherit;
            text-align: center;
        }
        .fs-sidebar-card {
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: rgba(21, 30, 45, 0.84);
            padding: 10px 10px;
            min-width: 0;
        }
        .fs-sidebar-footer {
            margin-top: auto;
            padding: 12px var(--fs-sidebar-pad-x) 0 var(--fs-sidebar-pad-x);
            border-top: 1px solid var(--fs-line);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .fs-portfolio-card {
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: rgba(21, 30, 45, 0.84);
            padding: 10px 10px;
            min-width: 0;
        }
        .fs-sidebar-kicker {
            color: var(--fs-muted);
            font-size: 0.64rem;
        }
        .fs-sidebar-value {
            color: var(--fs-ink);
            font-size: 0.82rem;
            font-weight: 720;
            margin-top: 0.15rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .fs-status-dot {
            width: 0.42rem;
            height: 0.42rem;
            border-radius: 999px;
            display: inline-block;
            margin-right: 0.32rem;
            background: var(--fs-teal);
            box-shadow: 0 0 0 3px rgba(37, 242, 199, 0.08);
        }
        .fs-user-row {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.12rem 0;
        }
        .fs-user-avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, var(--fs-blue), var(--fs-purple));
            color: #f8fbff;
            font-size: 0.68rem;
            font-weight: 820;
            flex: 0 0 auto;
        }
        .fs-user-copy {
            min-width: 0;
        }
        .fs-user-name {
            color: var(--fs-ink);
            font-size: 0.78rem;
            font-weight: 760;
            white-space: nowrap;
        }
        .fs-user-plan {
            color: var(--fs-muted);
            font-size: 0.64rem;
            margin-top: 0.12rem;
            white-space: nowrap;
        }

        .fs-topbar-shell {
            border: 1px solid var(--fs-line);
            border-radius: 14px;
            background: linear-gradient(180deg, rgba(16, 34, 55, 0.88), rgba(12, 25, 42, 0.9));
            padding: 12px 16px 10px 16px;
            margin: 0 0 var(--fs-gap-sm) 0;
        }
        .fs-topbar {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.65rem;
            margin: 0;
        }
        .fs-page-title {
            margin: 0;
            font-size: 1.18rem;
            font-weight: 760;
            line-height: 1.08;
        }
        .fs-page-subtitle {
            color: var(--fs-soft);
            margin-top: 0.2rem;
            font-size: 0.7rem;
        }
        .fs-badge-row {
            display: flex;
            align-items: center;
            gap: 0.36rem;
            flex-wrap: wrap;
            margin-top: 0.28rem;
        }
        .fs-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.32rem;
            border: 1px solid var(--fs-accent-line);
            background: var(--fs-accent-soft);
            color: #8ae7dd;
            border-radius: 999px;
            padding: 0.14rem 0.4rem;
            font-size: 0.6rem;
            font-weight: 720;
        }
        .fs-badge-live {
            animation: fs-pulse 1800ms var(--fs-ease) infinite;
        }
        .fs-badge-muted {
            color: var(--fs-soft);
            border-color: var(--fs-line);
            background: rgba(129, 166, 202, 0.08);
        }

        .fs-control-panel {
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: var(--fs-control-bg);
            padding: var(--fs-gap-md);
            margin: 0 0 var(--fs-gap-lg) 0;
            box-shadow: var(--fs-shadow);
        }
        .fs-control-shell {
            margin-bottom: var(--fs-gap-sm);
        }
        .fs-control-shell .fs-panel-header {
            margin-bottom: 0.28rem;
        }
        .fs-control-shell [data-testid="stHorizontalBlock"] {
            align-items: end;
        }
        .fs-control-caption {
            color: var(--fs-muted);
            font-size: 0.64rem;
            font-weight: 760;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            margin-bottom: 0.28rem;
        }
        .fs-control-caption-compact {
            margin: 0 0 var(--fs-gap-xs) 0;
        }

        .fs-card-grid {
            display: grid;
            gap: var(--fs-gap-md);
            grid-template-columns: repeat(auto-fit, minmax(178px, 1fr));
            margin: var(--fs-gap-md) 0;
        }
        .fs-metric-card,
        .fs-summary-stat,
        .fs-panel,
        .fs-rule-card,
        .fs-insight-card,
        .fs-empty-state {
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: var(--fs-card-bg);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
            transition: transform var(--fs-fast) var(--fs-ease), border-color var(--fs-fast) var(--fs-ease), background var(--fs-fast) var(--fs-ease), box-shadow var(--fs-fast) var(--fs-ease);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: transparent !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            margin: 0;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
            gap: var(--fs-gap-sm);
        }
        .fs-row-spacer {
            height: var(--fs-gap-sm);
            min-height: var(--fs-gap-sm);
        }
        .fs-row-spacer-sm {
            height: var(--fs-gap-xs);
            min-height: var(--fs-gap-xs);
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) {
            border: 1px solid var(--fs-line) !important;
            border-radius: var(--fs-radius) !important;
            background: var(--fs-panel-card-bg) !important;
            box-shadow: var(--fs-shadow);
            min-height: 0;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) > div {
            padding: var(--fs-gap-md) var(--fs-gap-lg) !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) {
            overflow-x: hidden !important;
            overflow-y: auto !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) [data-testid="stVerticalBlock"] {
            min-height: 0;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-track {
            background: transparent;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-thumb {
            background: rgba(129, 166, 202, 0.28);
            border-radius: 999px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-lean) {
            border: 1px solid var(--fs-line) !important;
            border-radius: var(--fs-radius) !important;
            background: var(--fs-panel-card-bg) !important;
            box-shadow: var(--fs-shadow) !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-lean) > div {
            padding: 0.45rem 0.55rem !important;
        }
        .fs-panel-lean .fs-panel-header {
            margin-bottom: 0.35rem;
        }
        .fs-panel-lean .fs-insight-card,
        .fs-panel-lean .fs-table-scroll,
        .fs-panel-lean .fs-kv-table,
        .fs-panel-lean .fs-empty-state {
            box-shadow: none !important;
        }

        /* FINSKILLOS_SCROLL_SCOPE_FIX_V4
           Only panels rendered with panel(..., scroll=True, height=...)
           become local vertical scroll areas. Tables own horizontal overflow only.
           Do not use overscroll-behavior: contain because it traps wheel chaining.
        */

        [data-testid="stMain"],
        section.main,
        [data-testid="stMainBlockContainer"],
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"],
        [data-testid="column"],
        [data-testid="column"] > div,
        div[data-testid="stElementContainer"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
            min-width: 0 !important;
            overscroll-behavior: auto !important;
        }

        [data-testid="stMain"],
        section.main {
            overflow-x: hidden !important;
            overscroll-behavior-y: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-panel-scroll)) {
            overflow: visible !important;
            overscroll-behavior: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-panel-scroll)) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-panel-scroll)) > div > [data-testid="stVerticalBlock"] {
            height: auto !important;
            max-height: none !important;
            min-height: 0 !important;
            overflow: visible !important;
            overscroll-behavior: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) {
            min-width: 0 !important;
            overflow: hidden !important;
            overscroll-behavior: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div {
            height: 100% !important;
            min-height: 0 !important;
            min-width: 0 !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div > [data-testid="stVerticalBlock"] {
            height: auto !important;
            min-height: 100% !important;
            min-width: 0 !important;
            overflow: visible !important;
            overscroll-behavior: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) .fs-panel-header {
            position: sticky;
            top: 0;
            z-index: 5;
            padding-bottom: var(--fs-gap-xs);
            background: linear-gradient(180deg, rgba(12, 27, 45, 0.98), rgba(12, 27, 45, 0.86));
            backdrop-filter: blur(6px);
        }

        .fs-table-scroll {
            display: block !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            max-height: none !important;
            overflow-x: auto !important;
            overflow-y: visible !important;
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: var(--fs-table-bg);
            overscroll-behavior: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        .fs-data-table,
        .fs-kv-table {
            width: max-content !important;
            min-width: 100% !important;
            border-collapse: separate;
            border-spacing: 0;
            table-layout: auto;
        }

        .fs-data-table th,
        .fs-data-table td,
        .fs-kv-table th,
        .fs-kv-table td {
            white-space: nowrap;
        }

        .fs-kv-table td:last-child {
            white-space: normal;
            min-width: 12rem;
        }

        .fs-data-table thead th,
        .fs-kv-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            background: var(--fs-table-header-bg);
            backdrop-filter: blur(6px);
        }

        div[data-testid="stDataFrame"],
        div[data-testid="stTable"],
        div[data-testid="stDataFrame"] > div,
        div[data-testid="stTable"] > div {
            max-width: 100% !important;
            min-width: 0 !important;
            overscroll-behavior: auto !important;
        }

        div[data-testid="stTable"] table {
            width: max-content !important;
            min-width: 100% !important;
        }


        /* FINSKILLOS_TABLE_BOTTOM_CLIP_FIX
           Add a small bottom breathing room for custom HTML tables.
           This prevents the last row/bottom border from being clipped by
           Streamlit border containers and local scroll panels.
        */

        .fs-table-scroll {
            margin-bottom: 10px !important;
            padding-bottom: 1px !important;
        }

        .fs-data-table,
        .fs-kv-table {
            margin-bottom: 0 !important;
        }

        .fs-data-table tbody tr:last-child td,
        .fs-kv-table tbody tr:last-child td {
            border-bottom: 1px solid var(--fs-line) !important;
            padding-bottom: 0.62rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div {
            padding-bottom: 12px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div > [data-testid="stVerticalBlock"] {
            padding-bottom: 4px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-panel-scroll)) {
            padding-bottom: 2px !important;
        }


        /* FINSKILLOS_OVERVIEW_FOOTER_V9_2
           Complete Overview footer replacement styles.
           This block is self-contained and does not rely on v9/v9.1.
        */

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) {
            margin-top: 4px !important;
            margin-bottom: 20px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) > div {
            padding-bottom: 16px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) [data-testid="stHorizontalBlock"] {
            align-items: stretch !important;
        }

        .fs-overview-rules-panel .fs-panel-header {
            margin-bottom: 8px;
        }

        .fs-overview-rule-strip {
            display: block;
            width: 100%;
        }

        .fs-overview-rule-divider {
            height: 1px;
            width: 100%;
            margin: 12px 0 12px 0;
            background: linear-gradient(
                90deg,
                rgba(25, 198, 180, 0.28),
                rgba(129, 166, 202, 0.12),
                rgba(129, 166, 202, 0.03)
            );
        }

        .fs-overview-stat-card {
            height: 82px;
            min-height: 82px;
            padding: 0.78rem 0.88rem;
            border: 1px solid rgba(129, 166, 202, 0.16);
            border-radius: 12px;
            background:
                radial-gradient(circle at 0% 0%, rgba(25, 198, 180, 0.10), transparent 11rem),
                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.04),
                0 8px 20px rgba(0, 0, 0, 0.12);
            overflow: hidden;
        }

        .fs-overview-stat-kicker {
            color: var(--fs-muted);
            font-size: 0.62rem;
            font-weight: 820;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            line-height: 1;
            margin-bottom: 0.46rem;
        }

        .fs-overview-stat-value {
            color: var(--fs-ink);
            font-size: 1.08rem;
            font-weight: 880;
            letter-spacing: -0.02em;
            line-height: 1.08;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .fs-overview-stat-caption {
            color: var(--fs-muted);
            font-size: 0.68rem;
            font-weight: 620;
            line-height: 1.22;
            margin-top: 0.38rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .fs-overview-stat-card[data-tone="teal"] .fs-overview-stat-value {
            color: var(--fs-teal);
        }

        .fs-overview-stat-card[data-tone="blue"] .fs-overview-stat-value {
            color: var(--fs-blue);
        }

        .fs-overview-stat-card[data-tone="purple"] .fs-overview-stat-value {
            color: var(--fs-purple);
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton {
            height: 82px !important;
            min-height: 82px !important;
            margin: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button {
            width: 100% !important;
            height: 82px !important;
            min-height: 82px !important;
            border-radius: 14px !important;
            font-size: 0.88rem !important;
            font-weight: 840 !important;
            letter-spacing: -0.01em;
            box-shadow:
                0 14px 30px rgba(17, 123, 140, 0.24),
                inset 0 1px 0 rgba(255, 255, 255, 0.14) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button p {
            font-size: 0.88rem !important;
            font-weight: 840 !important;
            line-height: 1 !important;
        }

        .fs-overview-report-unavailable {
            height: 82px;
            min-height: 82px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(245, 166, 35, 0.24);
            border-radius: 14px;
            background: rgba(245, 166, 35, 0.08);
        }

        .fs-overview-footer-end {
            height: 18px;
        }



        /* FINSKILLOS_OVERVIEW_FOOTER_V9_4
           Stronger Overview footer compaction.
           v9.3 was too conservative: the visible issue is mostly the footer
           panel min-height, not only outer margin.
        */

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) {
            margin-top: 6px !important;
            margin-bottom: 18px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) > div {
            padding-top: 12px !important;
            padding-bottom: 12px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) [data-testid="stVerticalBlock"] {
            gap: 8px !important;
        }

        .fs-overview-rules-panel .fs-panel-header {
            margin-bottom: 8px !important;
        }

        .fs-overview-rule-divider {
            margin: 8px 0 8px 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .fs-rule-chip {
            min-height: 48px !important;
            padding: 0.58rem 0.72rem !important;
        }

        .fs-overview-stat-card {
            height: 72px !important;
            min-height: 72px !important;
            padding: 0.66rem 0.78rem !important;
        }

        .fs-overview-stat-kicker {
            font-size: 0.6rem !important;
            margin-bottom: 0.38rem !important;
        }

        .fs-overview-stat-value {
            font-size: 1.08rem !important;
            line-height: 1.04 !important;
        }

        .fs-overview-stat-caption {
            font-size: 0.66rem !important;
            margin-top: 0.32rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton {
            height: 72px !important;
            min-height: 72px !important;
            margin: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button {
            height: 72px !important;
            min-height: 72px !important;
            border-radius: 13px !important;
            font-size: 1.08rem !important;
            font-weight: 900 !important;
            letter-spacing: -0.02em !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button p,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .stDownloadButton > button span {
            font-size: 1.08rem !important;
            font-weight: 900 !important;
            line-height: 1.05 !important;
        }

        .fs-overview-footer-end {
            height: 14px !important;
        }

        /* v5 dynamic min-height classes can keep the footer visually too tall.
           Override the specific v9.2/v9.4 footer height class only inside this panel. */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel.fs-panel-height-268),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel.fs-panel-height-226) {
            min-height: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel.fs-panel-height-268) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel.fs-panel-height-226) > div {
            min-height: 0 !important;
        }


        /* FINSKILLOS_OVERVIEW_FOOTER_V9_5
           Add explicit breathing room between the divider hline and the
           Rules/Coverage/Schema/Generate Report row.
        */

        .fs-overview-rule-divider {
            margin: 8px 0 6px 0 !important;
        }

        .fs-overview-stat-row-spacer {
            height: 18px;
            min-height: 10px;
            width: 100%;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-overview-rules-panel) .fs-overview-stat-row-spacer {
            display: block !important;
        }


        /* FINSKILLOS_APPLIED_RULES_LAYOUT_V11 */

        .fs-governance-grade {
            padding: 0.72rem 0.84rem;
            border: 1px solid rgba(129, 166, 202, 0.16);
            border-radius: 12px;
            background:
                radial-gradient(circle at 0% 0%, rgba(0, 212, 160, 0.10), transparent 10rem),
                linear-gradient(180deg, rgba(13, 28, 45, 0.96), rgba(7, 17, 31, 0.98));
            margin-bottom: 0.72rem;
        }

        .fs-governance-grade-label {
            color: var(--fs-soft);
            font-size: 0.76rem;
            font-weight: 760;
            margin-bottom: 0.36rem;
        }

        .fs-governance-grade-value {
            color: var(--fs-teal);
            font-size: 2rem;
            font-weight: 900;
            line-height: 1;
            letter-spacing: -0.04em;
        }

        .fs-rule-health-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 8px;
        }

        .fs-rule-health-strip > div {
            min-height: 72px;
            padding: 0.66rem 0.72rem;
            border: 1px solid rgba(129, 166, 202, 0.14);
            border-radius: 12px;
            background: rgba(7, 17, 31, 0.72);
        }

        .fs-rule-health-strip span {
            display: block;
            color: var(--fs-teal);
            font-size: 1.35rem;
            font-weight: 900;
            line-height: 1;
        }

        .fs-rule-health-strip small {
            display: block;
            color: var(--fs-muted);
            font-size: 0.66rem;
            font-weight: 760;
            margin-top: 0.36rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) .fs-data-table td,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) .fs-data-table th {
            vertical-align: top;
        }


        /* FINSKILLOS_APPLIED_RULES_LAYOUT_V11_1 */

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-governance-grade) {
            min-width: 0 !important;
        }

        .fs-rules-table-search-gap {
            height: 8px;
            min-height: 8px;
            width: 100%;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-rules-table-search-gap) [data-testid="stTextInput"] {
            margin-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-rules-table-search-gap) [data-testid="stTextInput"] input {
            min-height: 2.35rem !important;
            font-size: 0.82rem !important;
        }


        /* FINSKILLOS_INSIGHTS_FOOTER_SPACING_V12
           Prevent the global Skills.md expander from visually colliding with
           the Insights tab's final "Pinned Insights & Next Steps" row.
        */

        .fs-insights-footer-end {
            height: 28px;
            min-height: 28px;
            width: 100%;
        }

        /* Add breathing room only when the Insights tab emits the footer spacer. */
        div[data-testid="stElementContainer"]:has(.fs-insights-footer-end) {
            margin-bottom: 10px !important;
        }

        /* Pinned cards are usually rendered as rule-chip-like cards near the tab end.
           This keeps their row from visually touching the expander border. */
        div[data-testid="stHorizontalBlock"]:has(.fs-insight-next-card),
        div[data-testid="stHorizontalBlock"]:has(.fs-pinned-insight-card),
        div[data-testid="stHorizontalBlock"]:has(.fs-next-step-card) {
            margin-bottom: 12px !important;
        }

        /* Fallback: if the pinned cards reuse fs-rule-chip, give the last horizontal
           block before the Insights footer a little separation. */
        div[data-testid="stHorizontalBlock"]:has(+ div [class*="fs-insights-footer-end"]) {
            margin-bottom: 12px !important;
        }

        @keyframes fs-card-in {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fs-page-in {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fs-nav-lock {
            from { background: rgba(37, 242, 199, 0.04); }
            to { background: rgba(37, 242, 199, 0.12); }
        }
        @keyframes fs-pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(37, 242, 199, 0.0); }
            50% { box-shadow: 0 0 0 4px rgba(37, 242, 199, 0.08); }
        }
        .fs-metric-card:hover,
        .fs-panel:hover,
        .fs-rule-card:hover,
        .fs-insight-card:hover {
            border-color: var(--fs-accent-line);
            background: var(--fs-panel-hover);
            transform: translateY(-1px);
        }
        .fs-metric-card {
            min-height: 88px;
            padding: var(--fs-gap-md);
            display: flex;
            gap: var(--fs-gap-sm);
            align-items: flex-start;
            animation: fs-card-in 240ms ease both;
            overflow-wrap: normal;
            margin-bottom: 0.42rem;
        }
        .fs-metric-icon {
            width: 2rem;
            height: 2rem;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: linear-gradient(180deg, rgba(25, 198, 180, 0.18), rgba(36, 109, 185, 0.12));
            color: #6ee5d2;
            flex: 0 0 2rem;
            font-size: 0.62rem;
            font-weight: 900;
            letter-spacing: -0.02em;
            line-height: 1;
            overflow: hidden;
            overflow-wrap: normal;
            white-space: nowrap;
            word-break: keep-all;
        }
        .fs-metric-copy {
            min-width: 0;
        }
        .fs-metric-card[data-tone="blue"] .fs-metric-icon,
        .fs-metric-card[data-tone="blue"] .fs-metric-value { color: var(--fs-blue); }
        .fs-metric-card[data-tone="red"] .fs-metric-icon,
        .fs-metric-card[data-tone="red"] .fs-metric-value { color: var(--fs-red); }
        .fs-metric-card[data-tone="amber"] .fs-metric-icon,
        .fs-metric-card[data-tone="amber"] .fs-metric-value { color: var(--fs-amber); }
        .fs-metric-card[data-tone="purple"] .fs-metric-icon,
        .fs-metric-card[data-tone="purple"] .fs-metric-value { color: var(--fs-purple); }
        .fs-metric-label {
            color: var(--fs-soft);
            font-size: 0.68rem;
            font-weight: 680;
            margin-bottom: var(--fs-gap-xs);
        }
        .fs-metric-value {
            color: var(--fs-teal);
            font-size: 1.28rem;
            font-weight: 760;
            line-height: 1.05;
            overflow-wrap: anywhere;
        }
        .fs-metric-caption {
            color: var(--fs-muted);
            margin-top: var(--fs-gap-xs);
            font-size: 0.66rem;
        }
        .fs-summary-stat {
            min-height: 56px;
            padding: var(--fs-gap-sm) var(--fs-gap-md);
            display: flex;
            flex-direction: column;
            justify-content: center;
            overflow: hidden;
        }
        .fs-summary-label {
            color: var(--fs-ink);
            font-size: 0.82rem;
            font-weight: 760;
            line-height: 1.2;
            white-space: nowrap;
        }
        .fs-summary-value {
            color: var(--fs-soft);
            font-size: 0.86rem;
            line-height: 1.25;
            margin-top: var(--fs-gap-xs);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .fs-kv-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: var(--fs-gap-sm) 0 0 0;
            overflow: hidden;
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: var(--fs-table-bg);
            table-layout: fixed;
        }
        .fs-kv-table th,
        .fs-kv-table td {
            padding: 0.44rem 0.52rem;
            border-bottom: 1px solid rgba(129, 166, 202, 0.12);
            color: var(--fs-soft);
            font-size: 0.72rem;
            text-align: left;
            overflow-wrap: anywhere;
        }
        .fs-kv-table th {
            color: var(--fs-muted);
            background: var(--fs-table-header-bg);
            font-size: 0.66rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .fs-kv-table td:last-child {
            color: var(--fs-ink);
            font-weight: 720;
        }
        .fs-kv-table tr:last-child td {
            border-bottom: 0;
        }
        .fs-table-scroll {
            width: 100%;
            max-height: 100%;
            overflow: auto;
            border: 1px solid var(--fs-line);
            border-radius: var(--fs-radius);
            background: var(--fs-table-bg);
        }
        .fs-data-table {
            width: 100%;
            min-width: 480px;
            border-collapse: collapse;
            table-layout: auto;
        }
        .fs-data-table th,
        .fs-data-table td {
            padding: 0.46rem 0.54rem;
            border-bottom: 1px solid rgba(129, 166, 202, 0.12);
            color: var(--fs-soft);
            font-size: 0.7rem;
            text-align: left;
            vertical-align: top;
            white-space: nowrap;
        }
        .fs-data-table th {
            color: var(--fs-muted);
            background: var(--fs-table-header-bg);
            font-size: 0.64rem;
            font-weight: 760;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .fs-data-table td {
            max-width: 260px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .fs-data-table tr:last-child td {
            border-bottom: 0;
        }
        .fs-validation-list {
            display: flex;
            flex-direction: column;
            gap: var(--fs-gap-sm);
        }
        .fs-validation-row {
            display: grid;
            grid-template-columns: 1.85rem minmax(0, 1fr) auto;
            align-items: start;
            gap: 0.62rem;
            padding: 0.64rem;
            border: 1px solid rgba(129, 166, 202, 0.18);
            border-radius: var(--fs-radius);
            background: var(--fs-surface-tint);
        }
        .fs-validation-icon {
            width: 1.85rem;
            height: 1.85rem;
            border-radius: 8px;
            display: grid;
            place-items: center;
            color: #79dfd3;
            background: linear-gradient(180deg, rgba(25, 198, 180, 0.16), rgba(36, 109, 185, 0.1));
            font-weight: 850;
            flex: 0 0 auto;
        }
        .fs-validation-copy {
            min-width: 0;
        }
        .fs-validation-title {
            color: var(--fs-ink);
            font-size: 0.78rem;
            font-weight: 780;
            white-space: nowrap;
        }
        .fs-validation-step,
        .fs-validation-result {
            color: var(--fs-muted);
            font-size: 0.68rem;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }
        .fs-validation-result {
            color: var(--fs-soft);
            margin-top: 0.18rem;
        }
        .fs-panel {
            padding: var(--fs-gap-md) var(--fs-gap-lg);
            margin: 0;
        }
        .fs-panel-shell {
            height: var(--fs-panel-height, auto);
            display: flex;
            flex-direction: column;
        }
        .fs-panel-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.62rem;
            margin-bottom: 0.62rem;
            flex: 0 0 auto;
        }
        .fs-panel-title {
            color: var(--fs-ink);
            font-size: 0.86rem;
            font-weight: 760;
        }
        .fs-panel-subtitle {
            color: var(--fs-muted);
            font-size: 0.7rem;
            margin-top: 0.15rem;
        }
        .fs-panel-body {
            display: flex;
            flex-direction: column;
            gap: var(--fs-gap-sm);
            min-height: 0;
        }
        .fs-panel-scroll .fs-panel-body {
            flex: 1 1 auto;
            overflow-y: auto;
            padding-right: 4px;
        }
        .fs-panel-scroll .fs-panel-body::-webkit-scrollbar {
            width: 5px;
        }
        .fs-panel-scroll .fs-panel-body::-webkit-scrollbar-track {
            background: transparent;
        }
        .fs-panel-scroll .fs-panel-body::-webkit-scrollbar-thumb {
            background: rgba(129, 166, 202, 0.28);
            border-radius: 999px;
        }
        .fs-section {
            border-top: 1px solid var(--fs-line);
            padding-top: var(--fs-gap-lg);
            margin-top: var(--fs-gap-lg);
        }
        .fs-section-kicker {
            color: var(--fs-teal);
            font-size: 0.64rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .fs-section-title {
            color: var(--fs-ink);
            font-size: 1rem;
            font-weight: 760;
            margin: 2px 0 var(--fs-gap-md) 0;
        }
        .fs-rule-card {
            padding: var(--fs-gap-md);
            min-height: 100px;
            overflow-wrap: anywhere;
        }
        .fs-rule-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.6rem;
            margin-bottom: 0.42rem;
        }
        .fs-rule-id {
            color: var(--fs-ink);
            font-size: 0.8rem;
            font-weight: 780;
            white-space: nowrap;
        }
        .fs-rule-chip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            border: 1px solid var(--fs-line);
            border-radius: 10px;
            background: linear-gradient(180deg, rgba(14, 32, 52, 0.72), rgba(7, 17, 31, 0.76));
            padding: 0.42rem 0.52rem;
            min-height: 48px;
            margin-bottom: 0.45rem;
        }
        .fs-rule-chip-main {
            min-width: 0;
            display: flex;
            flex-direction: column;
            gap: 0.08rem;
        }
        .fs-rule-chip-id {
            color: var(--fs-ink);
            font-size: 0.72rem;
            font-weight: 820;
            white-space: nowrap;
        }
        .fs-rule-chip-title {
            color: var(--fs-muted);
            font-size: 0.62rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .fs-rule-description,
        .fs-insight-body {
            color: var(--fs-soft);
            font-size: 0.7rem;
        }
        .fs-status {
            display: inline-flex;
            border-radius: 999px;
            padding: 0.14rem 0.46rem;
            font-size: 0.62rem;
            font-weight: 780;
            letter-spacing: 0.01em;
            border: 1px solid rgba(118, 235, 219, 0.34);
            color: #7de4d8;
            background: rgba(25, 198, 180, 0.1);
            white-space: nowrap;
        }
        .fs-status-warning {
            border-color: rgba(244, 183, 64, 0.5);
            color: var(--fs-amber);
            background: rgba(244, 183, 64, 0.1);
        }
        .fs-status-danger {
            border-color: rgba(255, 91, 115, 0.5);
            color: var(--fs-red);
            background: rgba(255, 91, 115, 0.1);
        }
        .fs-insight-card {
            padding: var(--fs-gap-md);
            border-left: 3px solid var(--fs-teal);
            margin-bottom: var(--fs-gap-sm);
            overflow-wrap: anywhere;
            display: flex;
            flex-direction: column;
            gap: var(--fs-gap-sm);
            background:
                linear-gradient(180deg, rgba(18, 34, 52, 0.92), rgba(10, 22, 36, 0.96)),
                var(--fs-card-bg);
        }
        .fs-insight-selected {
            border-color: rgba(118, 235, 219, 0.44);
            box-shadow: 0 0 0 1px rgba(25, 198, 180, 0.18), 0 14px 30px rgba(10, 54, 67, 0.22);
            background: linear-gradient(180deg, rgba(24, 50, 72, 0.96), rgba(11, 25, 40, 0.98));
        }
        .fs-insight-card[data-category="caution"],
        .fs-insight-card[data-category="data_quality"] {
            border-left-color: var(--fs-amber);
        }
        .fs-insight-card[data-severity="HIGH"],
        .fs-insight-card[data-severity="WARNING"] {
            border-left-color: var(--fs-red);
        }
        .fs-insight-title {
            color: var(--fs-ink);
            font-size: 0.78rem;
            font-weight: 760;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            margin-bottom: 0;
            letter-spacing: -0.01em;
        }
        .fs-insight-row {
            display: flex;
            align-items: flex-start;
            gap: 0.52rem;
            border: 1px solid rgba(148, 163, 184, 0.12);
            border-radius: 10px;
            padding: 0.48rem 0.54rem;
            background: linear-gradient(180deg, rgba(14, 25, 39, 0.72), rgba(10, 19, 31, 0.76));
        }
        .fs-insight-row-fact {
            background: rgba(25, 198, 180, 0.08);
            border-color: rgba(25, 198, 180, 0.18);
        }
        .fs-insight-row-interpretation {
            background: rgba(69, 133, 214, 0.08);
            border-color: rgba(69, 133, 214, 0.18);
        }
        .fs-insight-row-caution {
            background: rgba(214, 150, 53, 0.08);
            border-color: rgba(214, 150, 53, 0.2);
        }
        .fs-insight-badge {
            flex: 0 0 auto;
            border-radius: 999px;
            padding: 0.16rem 0.48rem;
            font-size: 0.62rem;
            font-weight: 780;
            white-space: nowrap;
        }
        .fs-insight-row-fact .fs-insight-badge {
            color: #71e0d0;
            background: rgba(25, 198, 180, 0.14);
        }
        .fs-insight-row-interpretation .fs-insight-badge {
            color: var(--fs-blue);
            background: rgba(69, 133, 214, 0.14);
        }
        .fs-insight-row-caution .fs-insight-badge {
            color: var(--fs-amber);
            background: rgba(214, 150, 53, 0.14);
        }
        .fs-insight-row .fs-insight-body {
            min-width: 0;
            line-height: 1.45;
        }
        .fs-insight-compact {
            padding: 0.48rem 0.56rem !important;
            min-height: unset !important;
            border-left-width: 3px;
        }
        .fs-insight-compact .fs-insight-title {
            margin-bottom: 0.18rem !important;
        }
        .fs-insight-compact .fs-insight-body {
            font-size: 0.66rem !important;
            line-height: 1.35 !important;
            color: var(--fs-soft);
        }
        .fs-empty-state {
            padding: 1rem;
            text-align: left;
            min-height: 112px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        .fs-empty-state::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(37, 242, 199, 0.06), transparent 34%),
                repeating-linear-gradient(135deg, rgba(129, 166, 202, 0.04) 0 1px, transparent 1px 9px);
            pointer-events: none;
        }
        .fs-empty-title {
            color: var(--fs-ink);
            font-weight: 760;
            font-size: 0.9rem;
            position: relative;
        }
        .fs-empty-message {
            color: var(--fs-muted);
            margin-top: 0.3rem;
            font-size: 0.74rem;
            position: relative;
        }

        /* =========================
           FinSkillOS Density Pass
           ========================= */

        [data-testid="stMainBlockContainer"],
        .main .block-container,
        section.main > div.block-container {
            padding: 0.35rem 0.7rem 1rem 0.7rem !important;
            max-width: 1760px !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.48rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.55rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
            border-color: transparent !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0 !important;
        }

        .fs-row-spacer {
            height: 0.45rem;
            min-height: 0.45rem;
        }

        .fs-row-spacer-sm {
            height: 0.28rem;
            min-height: 0.28rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) {
            border: 1px solid var(--fs-line) !important;
            border-radius: 10px !important;
            background: var(--fs-panel-card-bg) !important;
            box-shadow: var(--fs-shadow);
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) > div {
            padding: 0.55rem 0.62rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-lean) {
            border: 1px solid var(--fs-line) !important;
            border-radius: 10px !important;
            background: var(--fs-panel-card-bg) !important;
            box-shadow: var(--fs-shadow) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-lean) > div {
            padding: 0.38rem 0.42rem !important;
        }

        .fs-panel-lean .fs-panel-header {
            margin-bottom: 0.28rem !important;
        }

        .fs-panel-lean .fs-insight-card,
        .fs-panel-lean .fs-table-scroll,
        .fs-panel-lean .fs-kv-table,
        .fs-panel-lean .fs-empty-state {
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] h4,
        div[data-testid="stVerticalBlockBorderWrapper"] h3 {
            margin-top: 0 !important;
            margin-bottom: 0.18rem !important;
            line-height: 1.15 !important;
        }

        div[data-testid="stCaptionContainer"] {
            margin-bottom: 0.28rem !important;
        }

        .fs-topbar {
            margin-bottom: 0.48rem !important;
        }

        .fs-badge-row {
            margin-top: 0.26rem !important;
            gap: 0.28rem !important;
        }

        .fs-control-caption-compact {
            margin: 0.04rem 0 0.18rem 0 !important;
        }

        .fs-metric-card {
            min-height: 64px !important;
            padding: 0.46rem 0.54rem !important;
            gap: 0.42rem !important;
        }

        .fs-metric-icon {
            width: 23px !important;
            height: 23px !important;
            border-radius: 6px !important;
        }

        .fs-metric-label {
            font-size: 0.58rem !important;
            margin-bottom: 0.14rem !important;
        }

        .fs-metric-value {
            font-size: 0.98rem !important;
        }

        .fs-metric-caption {
            font-size: 0.56rem !important;
            margin-top: 0.18rem !important;
        }

        .fs-rule-card {
            min-height: 82px !important;
            padding: 0.55rem !important;
        }

        .fs-rule-top {
            margin-bottom: 0.28rem !important;
        }

        .fs-rule-id {
            font-size: 0.72rem !important;
        }

        .fs-rule-description {
            font-size: 0.64rem !important;
            line-height: 1.35 !important;
        }

        .fs-insight-card {
            padding: 0.52rem !important;
            gap: 0.28rem !important;
            margin-bottom: 0.36rem !important;
        }

        .fs-insight-row {
            padding: 0.34rem 0.42rem !important;
            gap: 0.38rem !important;
        }

        .fs-insight-body {
            font-size: 0.64rem !important;
            line-height: 1.32 !important;
        }

        .fs-validation-row {
            padding: 0.48rem !important;
            gap: 0.45rem !important;
        }

        .fs-validation-icon {
            width: 1.55rem !important;
            height: 1.55rem !important;
        }

        .fs-data-table th,
        .fs-data-table td,
        .fs-kv-table th,
        .fs-kv-table td {
            padding: 0.34rem 0.42rem !important;
            font-size: 0.64rem !important;
        }

        div[data-testid="stPlotlyChart"] {
            min-height: unset !important;
        }

        @media (min-width: 1500px) {
            [data-testid="stMainBlockContainer"],
            .main .block-container,
            section.main > div.block-container {
                max-width: none;
                padding-left: 20px !important;
                padding-right: 20px !important;
            }
            div[data-testid="column"] {
                min-width: 0;
            }
        }

        @media (max-width: 980px) {
            :root {
                --fs-sidebar-width: 232px;
            }
            [data-testid="stMainBlockContainer"],
            .main .block-container,
            section.main > div.block-container {
                padding-left: 16px !important;
                padding-right: 16px !important;
                padding-top: 16px !important;
            }
            .fs-topbar {
                display: block;
            }
            .fs-topbar-shell {
                padding: 18px 18px 16px 18px;
            }
            .fs-page-title {
                font-size: 1.38rem;
            }
            .fs-control-panel {
                padding: 0.7rem;
            }
            .fs-card-grid {
                grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
            }
            .fs-metric-card {
                min-height: 96px;
                padding: 0.82rem;
            }
            .fs-metric-icon {
                width: 34px;
                height: 34px;
                border-radius: 10px;
            }
            .fs-metric-value {
                font-size: 1.16rem;
            }
        }

        @media (max-width: 760px) {
            [data-testid="stMainBlockContainer"],
            .main .block-container,
            section.main > div.block-container {
                padding-left: 12px !important;
                padding-right: 12px !important;
            }
            .fs-page-title {
                font-size: 1.16rem;
            }
            .fs-page-subtitle,
            .fs-badge,
            .fs-metric-caption,
            .fs-rule-description,
            .fs-insight-body {
                font-size: 0.72rem;
            }
            .fs-brand-title {
                font-size: 1.2rem;
            }
            .fs-sidebar-card {
                padding: 0.72rem;
            }
            .fs-sidebar-footer {
                padding: 10px var(--fs-sidebar-pad-x) 0 var(--fs-sidebar-pad-x);
            }
            div[data-testid="stPlotlyChart"] {
                min-height: 220px;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.001ms !important;
                transition-duration: 0.001ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if str(theme).lower() == "light":
        st.markdown(
            """
            <style>
            :root {
                --fs-bg: #f4f7fb;
                --fs-bg-soft: #eef4fb;
                --fs-sidebar: #edf3fa;
                --fs-panel: rgba(255, 255, 255, 0.94);
                --fs-panel-strong: rgba(255, 255, 255, 0.98);
                --fs-panel-hover: rgba(246, 250, 255, 0.98);
                --fs-card-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(247, 250, 252, 0.94));
                --fs-panel-card-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 250, 252, 0.95));
                --fs-control-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(242, 247, 252, 0.96));
                --fs-table-bg: rgba(255, 255, 255, 0.9);
                --fs-table-header-bg: rgba(226, 232, 240, 0.7);
                --fs-line: rgba(36, 48, 68, 0.12);
                --fs-line-strong: rgba(0, 151, 124, 0.28);
                --fs-ink: #162033;
                --fs-muted: #64748b;
                --fs-soft: #334155;
                --fs-teal: #009b83;
                --fs-cyan: #047fa8;
                --fs-blue: #2563eb;
                --fs-red: #dc3545;
                --fs-amber: #b7791f;
                --fs-purple: #7c3aed;
                --fs-green: #168a52;
                --fs-accent-strong: #0f9f95;
                --fs-accent-deep: #1d6fb1;
                --fs-accent-soft: rgba(15, 159, 149, 0.08);
                --fs-accent-line: rgba(15, 159, 149, 0.22);
                --fs-button-bg: linear-gradient(135deg, #16a29a 0%, #1e8ab3 52%, #2c75bf 100%);
                --fs-button-hover-bg: linear-gradient(135deg, #1ab0a4 0%, #2896bf 52%, #357ec7 100%);
                --fs-button-shadow: 0 8px 18px rgba(29, 111, 177, 0.14), inset 0 1px 0 rgba(255, 255, 255, 0.18);
                --fs-button-shadow-hover: 0 12px 22px rgba(29, 111, 177, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.2);
                --fs-surface-tint: linear-gradient(180deg, rgba(250, 252, 255, 0.98), rgba(242, 247, 251, 0.94));
                --fs-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
                --fs-glow: 0 0 0 1px rgba(0, 151, 124, 0.18), 0 8px 18px rgba(0, 151, 124, 0.06);
            }

            html, body, [data-testid="stAppViewContainer"] {
                background:
                    radial-gradient(circle at 18% 0%, rgba(0, 151, 124, 0.08), transparent 26rem),
                    radial-gradient(circle at 92% 20%, rgba(37, 99, 235, 0.08), transparent 24rem),
                    linear-gradient(135deg, #f7fbff 0%, #eef4fb 56%, #f8fafc 100%) !important;
                color: var(--fs-ink);
            }
            [data-testid="stHeader"] {
                background: rgba(248, 250, 252, 0.82);
                border-bottom: 1px solid var(--fs-line);
            }
            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(239, 246, 255, 0.98), rgba(248, 250, 252, 0.98)),
                    var(--fs-sidebar);
                border-right: 1px solid var(--fs-line);
            }
            div[data-testid="stMetric"],
            .fs-topbar-shell,
            .fs-metric-card,
            .fs-summary-stat,
            .fs-panel,
            .fs-rule-card,
            .fs-rule-chip,
            .fs-insight-card,
            .fs-empty-state,
            .fs-portfolio-card,
            .fs-sidebar-card {
                background: var(--fs-card-bg) !important;
                border-color: var(--fs-line) !important;
                box-shadow: var(--fs-shadow);
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: transparent !important;
                border-color: transparent !important;
                box-shadow: none !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) {
                background: var(--fs-panel-card-bg) !important;
                border-color: var(--fs-line) !important;
                box-shadow: var(--fs-shadow);
            }
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) {
                background: var(--fs-control-bg) !important;
                border-color: rgba(36, 48, 68, 0.14) !important;
            }
            .fs-kv-table,
            .fs-table-scroll,
            div[data-testid="stDataFrame"] {
                background: var(--fs-table-bg) !important;
                border-color: var(--fs-line) !important;
            }
            .fs-kv-table th,
            .fs-data-table th {
                background: var(--fs-table-header-bg) !important;
                color: var(--fs-muted) !important;
            }
            .fs-kv-table td,
            .fs-data-table td,
            [data-testid="stSidebar"] [role="radiogroup"] label p {
                color: var(--fs-soft) !important;
            }
            .fs-data-table td,
            .fs-kv-table td {
                border-color: rgba(36, 48, 68, 0.1) !important;
            }
            .fs-validation-row,
            .fs-insight-row,
            .fs-insight-selected {
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.9)) !important;
                border-color: var(--fs-line) !important;
            }
            .fs-insight-row-fact {
                background: rgba(0, 151, 124, 0.08) !important;
                border-color: rgba(0, 151, 124, 0.2) !important;
            }
            .fs-insight-row-interpretation {
                background: rgba(37, 99, 235, 0.08) !important;
                border-color: rgba(37, 99, 235, 0.18) !important;
            }
            .fs-insight-row-caution {
                background: rgba(183, 121, 31, 0.08) !important;
                border-color: rgba(183, 121, 31, 0.2) !important;
            }
            .fs-validation-icon,
            .fs-metric-icon {
                background: linear-gradient(180deg, rgba(15, 159, 149, 0.12), rgba(37, 99, 235, 0.08));
            }
            .fs-topbar,
            .fs-page-title,
            .fs-panel-title,
            .fs-section-title,
            .fs-metric-label,
            .fs-validation-title,
            .fs-rule-id,
            .fs-insight-title,
            h1, h2, h3, h4 {
                color: var(--fs-ink);
            }
            .fs-page-subtitle,
            .fs-panel-subtitle,
            .fs-metric-caption,
            .fs-validation-step,
            .fs-validation-result,
            .fs-rule-description,
            .fs-insight-body {
                color: var(--fs-muted);
            }
            [data-baseweb="select"] > div,
            [data-testid="stTextInput"] input,
            [data-testid="stTextArea"] textarea,
            [data-testid="stNumberInput"] input,
            [data-testid="stFileUploader"] section {
                background: rgba(255, 255, 255, 0.96) !important;
                border-color: var(--fs-line) !important;
                color: var(--fs-ink) !important;
            }
            [data-testid="stNumberInputContainer"] > div:last-child {
                background: rgba(255, 255, 255, 0.96) !important;
                background-color: rgba(255, 255, 255, 0.96) !important;
                border-color: var(--fs-line) !important;
            }
            [data-testid="stNumberInput"] button,
            [data-testid="stNumberInputStepDown"],
            [data-testid="stNumberInputStepUp"] {
                background: transparent !important;
                background-color: transparent !important;
                border-color: var(--fs-line) !important;
                color: var(--fs-soft) !important;
            }
            [data-testid="stWidgetLabel"] p {
                color: var(--fs-muted) !important;
            }
            [data-baseweb="select"] svg {
                color: var(--fs-muted) !important;
            }
            [data-testid="stFileUploader"] section button {
                background: rgba(239, 246, 255, 0.92) !important;
                color: var(--fs-soft) !important;
                border-color: var(--fs-line) !important;
            }
            [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
                color: var(--fs-soft);
            }
            [data-baseweb="popover"],
            [data-baseweb="menu"],
            [role="listbox"] {
                background: #ffffff !important;
                color: var(--fs-ink) !important;
                border-color: var(--fs-line) !important;
            }
            [data-baseweb="menu"] li,
            [role="option"] {
                color: var(--fs-ink) !important;
            }
            [data-baseweb="menu"] li:hover,
            [role="option"]:hover {
                background: rgba(0, 151, 124, 0.08) !important;
            }
            .stButton > button,
            .stDownloadButton > button {
                background: var(--fs-button-bg);
                color: #ffffff;
                border-color: var(--fs-accent-line);
                box-shadow: var(--fs-button-shadow);
            }
            .stButton > button:hover,
            .stDownloadButton > button:hover,
            [data-testid="stPopover"] > button:hover {
                background: var(--fs-button-hover-bg) !important;
                box-shadow: var(--fs-button-shadow-hover) !important;
            }
            .fs-control-shell [data-testid="stPopover"] > button,
            .fs-control-shell [data-testid="stPopover"] button {
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(241, 246, 251, 0.96)) !important;
                border-color: rgba(36, 48, 68, 0.12) !important;
                color: var(--fs-soft) !important;
                box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85), 0 6px 14px rgba(15, 23, 42, 0.06) !important;
            }
            .fs-control-shell [data-testid="stPopover"] > button:hover,
            .fs-control-shell [data-testid="stPopover"] button:hover,
            .fs-control-shell [data-testid="stPopover"] > button:focus,
            .fs-control-shell [data-testid="stPopover"] button:focus,
            .fs-control-shell [data-testid="stPopover"] > button:active,
            .fs-control-shell [data-testid="stPopover"] button:active,
            .fs-control-shell [data-testid="stPopover"] > button[aria-expanded="true"],
            .fs-control-shell [data-testid="stPopover"] button[aria-expanded="true"] {
                background: linear-gradient(180deg, rgba(255, 255, 255, 1), rgba(237, 244, 250, 0.98)) !important;
                border-color: var(--fs-accent-line) !important;
                color: var(--fs-ink) !important;
                box-shadow: 0 0 0 1px rgba(15, 159, 149, 0.1), 0 8px 18px rgba(29, 111, 177, 0.08) !important;
            }
            .fs-badge-muted {
                background: rgba(226, 232, 240, 0.74);
                color: var(--fs-soft);
            }

            /* =========================================================
               FinSkillOS final layout policy

               Folded into the base theme so the final app does not depend
               on a separate override module.
            ========================================================= */

            :root {
                --fs-polish-radius: 14px;
                --fs-polish-radius-sm: 11px;
                --fs-polish-gap: 12px;
            }

            [data-testid="stMainBlockContainer"],
            .main .block-container,
            section.main > div.block-container {
                padding-top: 12px !important;
                padding-bottom: 36px !important;
            }

            [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"],
            .main .block-container [data-testid="stVerticalBlock"] {
                gap: 12px !important;
            }

            [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"],
            .main .block-container [data-testid="stHorizontalBlock"] {
                gap: 12px !important;
                margin: 0 !important;
                align-items: stretch !important;
            }

            [data-testid="column"] > [data-testid="stVerticalBlock"] {
                gap: 10px !important;
            }

            .fs-topbar-shell {
                margin: 0 0 10px 0 !important;
                padding: 0 !important;
                border: 0 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
                overflow: visible !important;
            }

            .fs-topbar {
                padding: 36px 22px 24px 22px !important;
                border: 0 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
            }

            .fs-page-title {
                margin-top: 0 !important;
                margin-bottom: 18px !important;
                line-height: 1.04 !important;
                letter-spacing: 0 !important;
            }

            .fs-page-subtitle {
                margin-bottom: 9px !important;
            }

            .fs-topbar-meta,
            .fs-badge-row {
                gap: 7px !important;
            }

            .fs-badge {
                padding: 5px 9px !important;
                line-height: 1 !important;
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell),
            div[data-testid="stContainer"]:has(.fs-control-shell) {
                margin: 0 0 2px 0 !important;
                padding: 0 !important;
                border: 0 !important;
                border-top: 1px solid var(--fs-line) !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
                overflow: visible !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) > div,
            div[data-testid="stContainer"]:has(.fs-control-shell) > div {
                padding: 12px 0 8px 0 !important;
                border-bottom: 1px solid var(--fs-line) !important;
            }

            .fs-control-shell {
                margin: 0 !important;
                padding: 0 !important;
                border: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) .fs-panel-header,
            div[data-testid="stContainer"]:has(.fs-control-shell) .fs-panel-header {
                margin-bottom: 10px !important;
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) [data-testid="column"],
            div[data-testid="stContainer"]:has(.fs-control-shell) [data-testid="column"] {
                display: flex !important;
                align-items: flex-end !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) [data-testid="column"] > div,
            div[data-testid="stContainer"]:has(.fs-control-shell) [data-testid="column"] > div {
                width: 100% !important;
            }

            [data-testid="stWidgetLabel"] {
                min-height: 1rem !important;
                margin-bottom: 6px !important;
            }

            [data-testid="stWidgetLabel"] p {
                font-size: 0.68rem !important;
                line-height: 1 !important;
                font-weight: 760 !important;
            }

            [data-baseweb="select"] > div,
            [data-testid="stNumberInput"] input,
            [data-testid="stFileUploader"] section {
                min-height: 2.58rem !important;
            }

            [data-testid="stFileUploader"] {
                min-height: 2.58rem !important;
            }

            [data-testid="stFileUploader"] section {
                max-height: 2.58rem !important;
                padding: 0.38rem 0.64rem !important;
            }

            [data-testid="stNumberInput"] button {
                min-height: 2.58rem !important;
            }

            [data-testid="stPopover"] button svg,
            [data-testid="stPopover"] [data-testid="stIconMaterial"] {
                display: none !important;
            }

            [data-testid="stPopover"] > button,
            [data-testid="stPopover"] button {
                width: 2.58rem !important;
                min-width: 2.58rem !important;
                max-width: 2.58rem !important;
                height: 2.58rem !important;
                min-height: 2.58rem !important;
                padding: 0 !important;
                border-radius: 11px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                box-shadow: none !important;
            }

            .stButton > button,
            .stDownloadButton > button,
            [data-testid="stButton"] button,
            [data-testid="stDownloadButton"] button,
            [data-testid="stPopover"] > button,
            [data-testid="stPopover"] button {
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 0.38rem !important;
                line-height: 1 !important;
                text-align: center !important;
                vertical-align: middle !important;
            }

            [data-testid="stButton"] button,
            [data-testid="stDownloadButton"] button {
                min-height: 2.58rem !important;
                padding: 0.48rem 0.72rem !important;
            }

            [data-testid="stButton"] button[kind="primary"],
            [data-testid="stButton"] button[data-testid="baseButton-primary"] {
                padding-left: 0.82rem !important;
                padding-right: 0.82rem !important;
            }

            .stButton > button p,
            .stDownloadButton > button p,
            [data-testid="stButton"] button p,
            [data-testid="stDownloadButton"] button p,
            [data-testid="stPopover"] button p {
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                display: block !important;
                color: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
                line-height: 1.05 !important;
                text-align: center !important;
                white-space: normal !important;
                overflow-wrap: anywhere !important;
            }

            [data-testid="stPopover"] button p {
                margin: 0 !important;
                line-height: 1 !important;
                font-weight: 850 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                height: 100% !important;
            }

            [data-testid="stHorizontalBlock"]:has(.fs-metric-card) {
                gap: 12px !important;
                margin: 0 0 18px 0 !important;
                padding: 0 0 14px 0 !important;
                border: 0 !important;
                border-bottom: 1px solid var(--fs-line) !important;
                border-radius: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
                overflow: visible !important;
            }

            [data-testid="stHorizontalBlock"]:has(.fs-metric-card)
                + [data-testid="stHorizontalBlock"],
            [data-testid="stHorizontalBlock"]:has(.fs-metric-card)
                ~ [data-testid="stHorizontalBlock"]:has(.fs-panel-shell) {
                margin-top: 6px !important;
            }

            .fs-metric-card {
                min-height: 12px !important;
                padding: 12px 14px !important;
                border: 1px solid var(--fs-line) !important;
                border-radius: 12px !important;
                box-shadow: none !important;
                background: var(--fs-panel) !important;
                background-clip: padding-box !important;
            }

            .fs-metric-card:hover {
                border-color: var(--fs-line-strong, var(--fs-line)) !important;
                box-shadow: none !important;
            }

            .fs-metric-icon {
                width: 30px !important;
                height: 30px !important;
                min-width: 30px !important;
                border: 0 !important;
                box-shadow: none !important;
            }

            .fs-metric-label {
                line-height: 1.15 !important;
                margin-bottom: 4px !important;
            }

            .fs-metric-value {
                line-height: 1.08 !important;
                margin-bottom: 4px !important;
            }

            .fs-metric-caption {
                line-height: 1.25 !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell)),
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell)) {
                border: 1px solid var(--fs-line) !important;
                border-radius: var(--fs-polish-radius) !important;
                box-shadow: none !important;
                background: var(--fs-panel) !important;
                overflow: hidden !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll),
            div[data-testid="stContainer"]:has(.fs-panel-scroll) {
                min-height: 0 !important;
                overflow-x: hidden !important;
                overflow-y: auto !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div,
            div[data-testid="stContainer"]:has(.fs-panel-scroll) > div,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) [data-testid="stVerticalBlock"],
            div[data-testid="stContainer"]:has(.fs-panel-scroll) [data-testid="stVerticalBlock"] {
                min-height: 0 !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar,
            div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-track,
            div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar-track {
                background: transparent;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-thumb,
            div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar-thumb {
                background: rgba(129, 166, 202, 0.28);
                border-radius: 999px;
            }

            .fs-panel-shell {
                margin: 0 !important;
                padding: 0 !important;
                border: 0 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
                overflow: visible !important;
            }

            .fs-panel-header {
                margin-bottom: 9px !important;
                padding: 0 !important;
                border: 0 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
            }

            .fs-panel-title {
                line-height: 1.16 !important;
            }

            .fs-panel-subtitle {
                margin-top: 5px !important;
                line-height: 1.35 !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"],
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"] {
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.fs-panel-shell)),
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"]:not(:has(.fs-panel-shell)),
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.fs-panel-shell)),
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"]:not(:has(.fs-panel-shell)) {
                border: 0 !important;
                border-radius: 0 !important;
                background: transparent !important;
                box-shadow: none !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.fs-panel-shell)) > div,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"]:not(:has(.fs-panel-shell)) > div,
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.fs-panel-shell)) > div,
            div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
                div[data-testid="stContainer"]:not(:has(.fs-panel-shell)) > div {
                padding-left: 0 !important;
                padding-right: 0 !important;
            }

            [data-testid="stPlotlyChart"],
            [data-testid="stPlotlyChart"] > div,
            [data-testid="stPlotlyChart"] iframe,
            .js-plotly-plot,
            .plot-container,
            .svg-container {
                border: 0 !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                background: transparent !important;
            }

            .fs-table-scroll,
            .fs-kv-table {
                border: 0 !important;
                border-radius: var(--fs-polish-radius-sm) !important;
                box-shadow: none !important;
                background: transparent !important;
                overflow-x: auto !important;
                overflow-y: auto !important;
            }

            .fs-kv-table,
            .fs-data-table {
                border: 0 !important;
                border-radius: var(--fs-polish-radius-sm) !important;
                box-shadow: none !important;
                background: transparent !important;
                overflow: visible !important;
            }

            .fs-kv-table thead,
            .fs-data-table thead,
            .fs-kv-table tbody,
            .fs-data-table tbody,
            .fs-kv-table tr,
            .fs-data-table tr,
            .fs-kv-table th,
            .fs-kv-table td,
            .fs-data-table th,
            .fs-data-table td {
                border: 0 !important;
                box-shadow: none !important;
            }

            .fs-kv-table th,
            .fs-kv-table td,
            .fs-data-table th,
            .fs-data-table td {
                padding-top: 9px !important;
                padding-bottom: 9px !important;
            }

            .fs-summary-stat,
            .fs-rule-card,
            .fs-rule-chip,
            .fs-insight-card,
            .fs-empty-state,
            .fs-validation-row,
            .fs-portfolio-card,
            .fs-sidebar-card,
            .fs-sample-help {
                border: 0 !important;
                box-shadow: none !important;
            }

            .fs-empty-state {
                padding: 18px !important;
                border-radius: var(--fs-polish-radius-sm) !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-summary-stat,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-rule-card,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-rule-chip,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-insight-card,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-empty-state,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-table-scroll,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-kv-table,
            div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-data-table {
                border: 0 !important;
                box-shadow: none !important;
            }

            .fs-sidebar-card {
                box-shadow: none !important;
            }

            div[data-testid="stMarkdownContainer"] h3 {
                margin-top: 8px !important;
                margin-bottom: 8px !important;
            }

            div[data-testid="stMarkdownContainer"] h5 {
                margin-top: 12px !important;
                margin-bottom: 7px !important;
            }

            div[data-testid="stMarkdownContainer"] p {
                margin-bottom: 0.45rem !important;
            }

            .fs-row-spacer {
                height: 12px !important;
            }

            .fs-row-spacer-sm {
                height: 8px !important;
            }

            [data-testid="stExpander"] {
                border-color: var(--fs-line) !important;
                box-shadow: none !important;
            }

            [data-testid="stDownloadButton"] button,
            [data-testid="stButton"] button {
                box-shadow: none !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
        /* =========================================================
           Shared container flattening

           Keep one visible panel container. Content inside panels uses
           tinted surfaces without drawing another bordered container.
        ========================================================= */

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell)),
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell)) {
            border: 1px solid var(--fs-line) !important;
            border-radius: 14px !important;
            background: var(--fs-panel) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell)) > div,
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell)) > div {
            padding: 12px 14px !important;
        }

        .fs-panel-shell,
        .fs-panel-header {
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        .fs-panel-shell {
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }

        .fs-panel-header {
            margin-bottom: 9px !important;
            padding: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stContainer"],
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stContainer"] {
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stContainer"] > div,
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stVerticalBlockBorderWrapper"] > div,
        div[data-testid="stContainer"]:has(.fs-panel-shell):not(:has(.fs-control-shell))
            div[data-testid="stContainer"] > div {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll),
        div[data-testid="stContainer"]:has(.fs-panel-scroll) {
            min-height: 0 !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) > div,
        div[data-testid="stContainer"]:has(.fs-panel-scroll) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll) [data-testid="stVerticalBlock"],
        div[data-testid="stContainer"]:has(.fs-panel-scroll) [data-testid="stVerticalBlock"] {
            min-height: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar,
        div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-track,
        div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar-track {
            background: transparent;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-scroll)::-webkit-scrollbar-thumb,
        div[data-testid="stContainer"]:has(.fs-panel-scroll)::-webkit-scrollbar-thumb {
            background: rgba(129, 166, 202, 0.28);
            border-radius: 999px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-summary-stat,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-rule-card,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-rule-chip,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-insight-card,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-empty-state,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-validation-row,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-table-scroll,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-kv-table,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-data-table,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-summary-stat,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-rule-card,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-rule-chip,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-insight-card,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-empty-state,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-validation-row,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-table-scroll,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-kv-table,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-data-table {
            border: 0 !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-insight-card,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-insight-card {
            border-left: 0 !important;
            border-radius: 8px !important;
            background: var(--fs-table-bg) !important;
            transform: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-insight-card:hover,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-insight-card:hover {
            border-color: transparent !important;
            background: var(--fs-panel-hover) !important;
            transform: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-insight-row,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-insight-row {
            border: 0 !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-table-scroll,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-table-scroll,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-panel-shell) .fs-kv-table,
        div[data-testid="stContainer"]:has(.fs-panel-shell) .fs-kv-table {
            background: transparent !important;
        }

        [data-testid="stPlotlyChart"],
        [data-testid="stPlotlyChart"] > div,
        [data-testid="stPlotlyChart"] iframe,
        .js-plotly-plot,
        .plot-container,
        .svg-container {
            border: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        /* Final controls pass: stable alignment first, decoration second. */

        .fs-control-field-label {
            position: relative;
            z-index: 20;
            display: inline-flex;
            align-items: center;
            gap: 0.34rem;
            max-width: 100%;
            height: 1rem;
            margin: 0 0 6px 0;
            color: var(--fs-muted);
            font-size: 0.68rem;
            font-weight: 760;
            line-height: 1;
            letter-spacing: 0.01em;
            white-space: nowrap;
        }

        .fs-control-help {
            width: 0.92rem;
            height: 0.92rem;
            border-radius: 999px;
            display: inline-grid;
            place-items: center;
            flex: 0 0 auto;
            cursor: help;
            border: 1px solid var(--fs-accent-line);
            background: var(--fs-accent-soft);
            color: var(--fs-teal);
            font-size: 0.62rem;
            font-weight: 860;
            line-height: 1;
            outline: none;
        }

        .fs-control-help-card {
            position: absolute;
            left: 0;
            top: calc(100% + 8px);
            z-index: 9999;
            display: none;
            width: max-content;
            min-width: min(22rem, calc(100vw - 48px));
            max-width: min(38rem, calc(100vw - 48px));
            padding: 0.72rem 0.82rem;
            border: 1px solid var(--fs-line);
            border-radius: 10px;
            background: var(--fs-panel-card-bg);
            color: var(--fs-ink);
            box-shadow: var(--fs-shadow);
            white-space: normal;
            overflow: visible;
        }

        .fs-control-field-label:hover .fs-control-help-card,
        .fs-control-field-label:focus-within .fs-control-help-card {
            display: block;
        }

        .fs-control-help-title {
            color: var(--fs-ink);
            font-size: 0.82rem;
            font-weight: 820;
            line-height: 1.24;
            margin-bottom: 0.34rem;
        }

        .fs-control-help-body {
            color: var(--fs-soft);
            font-size: 0.76rem;
            font-weight: 560;
            line-height: 1.52;
            white-space: normal;
            overflow: visible;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell),
        div[data-testid="stContainer"]:has(.fs-control-shell) {
            overflow: visible !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.fs-control-shell) [data-testid="column"],
        div[data-testid="stContainer"]:has(.fs-control-shell) [data-testid="column"] {
            min-width: 0 !important;
            align-items: flex-end !important;
        }

        .fs-control-shell [data-testid="stWidgetLabel"] {
            min-height: 1rem !important;
            margin-bottom: 6px !important;
        }

        .fs-control-shell [data-testid="stWidgetLabel"] p {
            max-width: 100% !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .fs-control-shell [data-testid="stWidgetLabel"] [data-testid="stTooltipHoverTarget"],
        .fs-control-shell [data-testid="stWidgetLabel"] svg,
        .fs-control-shell [data-testid="stWidgetLabel"] [data-testid="stIconMaterial"] {
            color: var(--fs-teal) !important;
            fill: currentColor !important;
            opacity: 1 !important;
        }

        .fs-control-shell [data-testid="stWidgetLabel"] [data-testid="stTooltipHoverTarget"] {
            width: 0.92rem !important;
            height: 0.92rem !important;
            border-radius: 999px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: var(--fs-accent-soft) !important;
            box-shadow: inset 0 0 0 1px var(--fs-accent-line) !important;
        }

        [data-baseweb="tooltip"],
        [data-baseweb="tooltip"] > div {
            max-width: 34rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 10px !important;
            background: var(--fs-panel-card-bg) !important;
            color: var(--fs-ink) !important;
            box-shadow: var(--fs-shadow) !important;
            line-height: 1.5 !important;
        }

        .fs-control-shell [data-baseweb="select"] > div,
        .fs-control-shell [data-testid="stNumberInput"] input,
        .fs-control-shell [data-testid="stFileUploader"] section,
        .fs-control-shell [data-testid="stButton"] button {
            min-height: 2.62rem !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] {
            height: 2.62rem !important;
            min-height: 2.62rem !important;
            min-width: 0 !important;
            position: relative !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section {
            position: relative !important;
            max-height: 2.62rem !important;
            padding: 0.34rem 0.5rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 10px !important;
            background: var(--fs-surface-tint) !important;
            color: var(--fs-ink) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section:hover,
        .fs-control-shell [data-testid="stFileUploader"] section:focus-within {
            border-color: var(--fs-accent-line) !important;
            box-shadow: 0 0 0 1px rgba(25, 198, 180, 0.1) !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section > div {
            width: 100% !important;
            min-width: 0 !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.42rem !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {
            flex: 1 1 auto !important;
            min-width: 0 !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
            content: "CSV file" !important;
            display: block !important;
            max-width: 100% !important;
            color: var(--fs-soft) !important;
            font-size: 0.72rem !important;
            font-weight: 760 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .fs-control-shell [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"])
            [data-testid="stFileUploaderDropzoneInstructions"]::before {
            content: "" !important;
        }

        .fs-control-shell [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"])
            [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section button {
            flex: 0 0 auto !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 1.74rem !important;
            height: 1.74rem !important;
            min-width: 2rem !important;
            width: 2rem !important;
            padding: 0 !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 8px !important;
            background: var(--fs-panel) !important;
            color: var(--fs-soft) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section button:hover {
            border-color: var(--fs-accent-line) !important;
            color: var(--fs-ink) !important;
            background: var(--fs-accent-soft) !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section button p {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0 0 0 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] section button::before {
            content: "";
            display: block;
            width: 0.94rem;
            height: 0.94rem;
            background: currentColor;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.25' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M12 18v-6'/%3E%3Cpath d='M9 15l3-3 3 3'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.25' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M12 18v-6'/%3E%3Cpath d='M9 15l3-3 3 3'/%3E%3C/svg%3E") center / contain no-repeat;
        }

        .fs-control-shell [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section button {
            display: none !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
            display: flex !important;
            align-items: center !important;
            gap: 0.38rem !important;
            position: absolute !important;
            left: 0.42rem !important;
            right: 0.42rem !important;
            top: 50% !important;
            width: auto !important;
            height: 1.84rem !important;
            min-height: 1.84rem !important;
            margin: 0 !important;
            padding: 0.22rem 1.64rem 0.22rem 2rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 8px !important;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0)),
                var(--fs-panel) !important;
            color: var(--fs-ink) !important;
            box-shadow: none !important;
            overflow: hidden !important;
            transform: translateY(-50%) !important;
            z-index: 3 !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"]::before {
            content: "";
            position: absolute;
            left: 0.54rem;
            top: 50%;
            width: 0.98rem;
            height: 0.98rem;
            transform: translateY(-50%);
            background: var(--fs-teal);
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            pointer-events: none;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div {
            min-width: 0 !important;
            max-width: 100% !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
            max-width: 100% !important;
            color: var(--fs-ink) !important;
            font-size: 0.68rem !important;
            font-weight: 700 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button {
            position: absolute !important;
            right: 0.34rem !important;
            top: 50% !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 1.12rem !important;
            min-width: 1.12rem !important;
            height: 1.12rem !important;
            min-height: 1.12rem !important;
            padding: 0 !important;
            transform: translateY(-50%) !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 999px !important;
            background: var(--fs-surface-tint) !important;
            color: var(--fs-muted) !important;
            box-shadow: none !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button:hover {
            border-color: rgba(240, 81, 81, 0.3) !important;
            background: rgba(240, 81, 81, 0.1) !important;
            color: var(--fs-red) !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button svg {
            width: 0.72rem !important;
            height: 0.72rem !important;
            color: currentColor !important;
            fill: currentColor !important;
        }

        .fs-control-shell [data-testid="stFileUploader"] small {
            display: none !important;
        }

        /* Specificity guard: older uploader theme blocks use html body
           selectors, so this scoped pass must outrank them in both themes. */
        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stWidgetLabel"] [data-testid="stTooltipHoverTarget"],
        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stWidgetLabel"] svg,
        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stWidgetLabel"] [data-testid="stIconMaterial"] {
            color: var(--fs-teal) !important;
            fill: currentColor !important;
            opacity: 1 !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] {
            height: 2.62rem !important;
            min-height: 2.62rem !important;
            min-width: 0 !important;
            position: relative !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] section {
            position: relative !important;
            min-height: 2.62rem !important;
            max-height: 2.62rem !important;
            padding: 0.34rem 0.5rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 10px !important;
            background: var(--fs-surface-tint) !important;
            color: var(--fs-ink) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] section > div {
            width: 100% !important;
            min-width: 0 !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.42rem !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {
            flex: 1 1 auto !important;
            min-width: 0 !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"]::before {
            content: "CSV file" !important;
            display: block !important;
            max-width: 100% !important;
            color: var(--fs-soft) !important;
            font-size: 0.72rem !important;
            font-weight: 760 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] section button {
            flex: 0 0 auto !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 1.74rem !important;
            height: 1.74rem !important;
            min-width: 2rem !important;
            width: 2rem !important;
            padding: 0 !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 8px !important;
            background: var(--fs-panel) !important;
            color: var(--fs-soft) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] section button p {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0 0 0 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] section button::before {
            content: "";
            display: block;
            width: 0.94rem;
            height: 0.94rem;
            background: currentColor;
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.25' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M12 18v-6'/%3E%3Cpath d='M9 15l3-3 3 3'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.25' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M12 18v-6'/%3E%3Cpath d='M9 15l3-3 3 3'/%3E%3C/svg%3E") center / contain no-repeat;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"]:has([data-testid="stFileUploaderFile"]) section button {
            display: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] {
            display: flex !important;
            align-items: center !important;
            gap: 0.38rem !important;
            position: absolute !important;
            left: 0.42rem !important;
            right: 0.42rem !important;
            top: 50% !important;
            width: auto !important;
            height: 1.84rem !important;
            min-height: 1.84rem !important;
            margin: 0 !important;
            padding: 0.22rem 1.64rem 0.22rem 2rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 8px !important;
            background: var(--fs-panel) !important;
            color: var(--fs-ink) !important;
            box-shadow: none !important;
            overflow: hidden !important;
            transform: translateY(-50%) !important;
            z-index: 3 !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"]::before {
            content: "";
            position: absolute;
            left: 0.54rem;
            top: 50%;
            width: 0.98rem;
            height: 0.98rem;
            transform: translateY(-50%);
            background: var(--fs-teal);
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            pointer-events: none;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div:first-child {
            display: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] > div {
            min-width: 0 !important;
            max-width: 100% !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
            max-width: 100% !important;
            color: var(--fs-ink) !important;
            font-size: 0.68rem !important;
            font-weight: 700 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button {
            position: absolute !important;
            right: 0.34rem !important;
            top: 50% !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 1.12rem !important;
            min-width: 1.12rem !important;
            height: 1.12rem !important;
            min-height: 1.12rem !important;
            padding: 0 !important;
            transform: translateY(-50%) !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 999px !important;
            background: var(--fs-surface-tint) !important;
            color: var(--fs-muted) !important;
            box-shadow: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] button:hover {
            border-color: rgba(240, 81, 81, 0.3) !important;
            background: rgba(240, 81, 81, 0.1) !important;
            color: var(--fs-red) !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] small {
            display: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] > div:has(.stFileUploaderFile) {
            position: absolute !important;
            left: 0.42rem !important;
            right: 0.42rem !important;
            top: 50% !important;
            z-index: 5 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
            transform: translateY(-50%) !important;
            pointer-events: none;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] > div:has(.stFileUploaderFile) ul,
        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] > div:has(.stFileUploaderFile) li {
            margin: 0 !important;
            padding: 0 !important;
            list-style: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] .stFileUploaderFile {
            position: relative !important;
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
            height: 1.84rem !important;
            min-height: 1.84rem !important;
            margin: 0 !important;
            padding: 0.22rem 1.64rem 0.22rem 2rem !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 8px !important;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0)),
                var(--fs-panel) !important;
            color: var(--fs-ink) !important;
            box-shadow: none !important;
            overflow: hidden !important;
            pointer-events: auto;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] .stFileUploaderFile::before {
            content: "";
            position: absolute;
            left: 0.54rem;
            top: 50%;
            width: 0.98rem;
            height: 0.98rem;
            transform: translateY(-50%);
            background: var(--fs-teal);
            -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/%3E%3Cpath d='M14 2v6h6'/%3E%3Cpath d='M8 13h8'/%3E%3Cpath d='M8 17h5'/%3E%3C/svg%3E") center / contain no-repeat;
            pointer-events: none;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] .stFileUploaderFile > div:first-child {
            display: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] .stFileUploaderFileData {
            min-width: 0 !important;
            flex: 1 1 auto !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] .stFileUploaderFileName {
            max-width: 100% !important;
            margin: 0 !important;
            color: var(--fs-ink) !important;
            font-size: 0.68rem !important;
            font-weight: 720 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            white-space: nowrap !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] {
            position: absolute !important;
            right: 0.34rem !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 1.12rem !important;
            height: 1.12rem !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button {
            width: 1.12rem !important;
            min-width: 1.12rem !important;
            height: 1.12rem !important;
            min-height: 1.12rem !important;
            padding: 0 !important;
            border: 1px solid var(--fs-line) !important;
            border-radius: 999px !important;
            background: var(--fs-surface-tint) !important;
            color: var(--fs-muted) !important;
            box-shadow: none !important;
        }

        html body [data-testid="stAppViewContainer"] .fs-control-shell [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] button:hover {
            border-color: rgba(240, 81, 81, 0.3) !important;
            background: rgba(240, 81, 81, 0.1) !important;
            color: var(--fs-red) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(fig: go.Figure) -> go.Figure:
    """Apply the shared chart treatment for the selected shell theme."""

    is_light = str(st.session_state.get("dashboard_theme", "Dark")).lower() == "light"
    template = "plotly_white" if is_light else "plotly_dark"
    font_color = "#334155" if is_light else "#b8c4d4"
    muted_color = "#64748b" if is_light else "#7a8ba0"
    grid_color = "rgba(51, 65, 85, 0.12)" if is_light else "rgba(129, 166, 202, 0.12)"
    zero_color = "rgba(51, 65, 85, 0.18)" if is_light else "rgba(129, 166, 202, 0.2)"
    plot_bg = "rgba(0,0,0,0)"
    hover_bg = "#ffffff" if is_light else "#151e2d"
    hover_border = "rgba(51,65,85,0.18)" if is_light else "rgba(255,255,255,0.14)"

    fig.update_layout(
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=plot_bg,
        font=dict(color=font_color, family="DM Sans, Aptos, Segoe UI, sans-serif", size=11),
        colorway=PLOTLY_COLORS,
        margin=dict(l=8, r=8, t=18, b=8),
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10, color=muted_color),
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=hover_bg, bordercolor=hover_border, font_size=11),
    )
    fig.update_xaxes(gridcolor=grid_color, zerolinecolor=zero_color, tickfont=dict(size=10, color=muted_color), title_font=dict(size=11, color=muted_color))
    fig.update_yaxes(gridcolor=grid_color, zerolinecolor=zero_color, tickfont=dict(size=10, color=muted_color), title_font=dict(size=11, color=muted_color))
    return fig
