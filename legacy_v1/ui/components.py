"""Reusable UI components for FinSkillOS."""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from typing import Iterable, Iterator, Sequence

import streamlit as st


TONE_BY_SEVERITY = {
    "INFO": "default",
    "LOW": "default",
    "MEDIUM": "warning",
    "MODERATE": "warning",
    "WARNING": "warning",
    "HIGH": "danger",
    "VERY HIGH": "danger",
    "ERROR": "danger",
}


def _html(value: object) -> str:
    return escape("" if value is None else str(value))

def vspace(px: int = 14) -> None:
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)

def status_badge(text: str, tone: str = "default") -> str:
    css_class = "fs-status"
    if tone == "warning":
        css_class += " fs-status-warning"
    elif tone == "danger":
        css_class += " fs-status-danger"
    return f'<span class="{css_class}">{_html(text)}</span>'


def metric_card(label: str, value: str, caption: str, tone: str = "teal", icon: str = "◇") -> None:
    st.markdown(
        f"""
        <div class="fs-metric-card" data-tone="{_html(tone)}">
          <div class="fs-metric-icon">{_html(icon)}</div>
          <div class="fs-metric-copy">
            <div class="fs-metric-label">{_html(label)}</div>
            <div class="fs-metric-value">{_html(value)}</div>
            <div class="fs-metric-caption">{_html(caption)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_stat_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="fs-summary-stat">
          <div class="fs-summary-label">{_html(label)}</div>
          <div class="fs-summary-value">{_html(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def key_value_table(rows: Iterable[dict[str, object]], key_label: str = "Item", value_label: str = "Value") -> None:
    """Render compact key/value data without Streamlit's bright dataframe chrome."""

    body = "".join(
        f"""
        <tr>
          <td>{_html(row.get("item", ""))}</td>
          <td>{_html(row.get("value", ""))}</td>
        </tr>
        """
        for row in rows
    )
    st.markdown(
        f"""
        <div class="fs-table-scroll fs-kv-scroll" role="region" aria-label="Scrollable key value table" tabindex="0">
          <table class="fs-kv-table">
            <thead>
              <tr>
                <th>{_html(key_label)}</th>
                <th>{_html(value_label)}</th>
              </tr>
            </thead>
            <tbody>{body}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_data_table(rows: Iterable[dict[str, object]], columns: Sequence[str] | None = None, max_rows: int = 10) -> None:
    """Render a compact dark table for small dashboard summaries."""

    row_list = list(rows)[:max_rows]
    if not row_list:
        empty_state("No Rows Available", "This table has no records to display.")
        return
    headers = list(columns or row_list[0].keys())
    header_html = "".join(f"<th>{_html(header)}</th>" for header in headers)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{_html(row.get(header, ''))}</td>" for header in headers) + "</tr>"
        for row in row_list
    )
    st.markdown(
        f"""
        <div class="fs-table-scroll" role="region" aria-label="Scrollable data table" tabindex="0">
          <table class="fs-data-table">
            <thead><tr>{header_html}</tr></thead>
            <tbody>{body_html}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def rule_validation_list(records: Iterable[dict[str, object]], limit: int = 6) -> None:
    """Render readable rule validation rows for side panels."""

    record_list = list(records)[:limit]
    if not record_list:
        empty_state("No Rules Recorded", "No matching validation rules were recorded.")
        return

    rows = []
    for record in record_list:
        severity = str(record.get("severity", "INFO"))
        tone = TONE_BY_SEVERITY.get(severity.upper(), "default")
        status = "Review" if severity.upper() == "WARNING" else "Passed"
        rule_id = _html(record.get("rule_id", "RULE"))
        step = _html(record.get("step", "Validation rule"))
        result = _html(record.get("result", "Executed"))
        rows.append(
            '<div class="fs-validation-row">'
            f'<div class="fs-validation-icon">{rule_id[:1]}</div>'
            '<div class="fs-validation-copy">'
            f'<div class="fs-validation-title">{rule_id}</div>'
            f'<div class="fs-validation-step">{step}</div>'
            f'<div class="fs-validation-result">{result}</div>'
            "</div>"
            f"{status_badge(status, tone)}"
            "</div>"
        )

    st.markdown(f'<div class="fs-validation-list">{"".join(rows)}</div>', unsafe_allow_html=True)


@contextmanager
def panel(
    title: str,
    subtitle: str | None = None,
    action: str | None = None,
    *,
    height: int | None = None,
    scroll: bool = False,
    body_class: str | None = None,
) -> Iterator[None]:
    action_html = f"<div>{action}</div>" if action else ""
    subtitle_html = f'<div class="fs-panel-subtitle">{_html(subtitle)}</div>' if subtitle else ""
    class_names = ["fs-panel-shell"]
    use_local_scroll = scroll and height is not None
    height_class = f"fs-panel-height-{int(height)}" if height is not None else None
    if height_class:
        class_names.append(height_class)
    if use_local_scroll:
        class_names.append("fs-panel-scroll")
    if body_class:
        class_names.append(body_class)

    # Passing height to st.container creates a local scroll container in Streamlit.
    # Only explicit scroll panels receive height; all other panels remain in page flow.
    container_height = height if use_local_scroll else None
    visual_height_css = ""
    if height_class and not use_local_scroll:
        height_px = int(height)
        visual_height_css = (
            "<style>"
            f'div[data-testid="stVerticalBlockBorderWrapper"]:has(.{height_class}):not(:has(.fs-panel-scroll)) '
            f'{{ min-height: {height_px}px !important; }}'
            f'div[data-testid="stVerticalBlockBorderWrapper"]:has(.{height_class}):not(:has(.fs-panel-scroll)) > div '
            f'{{ min-height: calc({height_px}px - 2px) !important; }}'
            f'div[data-testid="stVerticalBlockBorderWrapper"]:has(.{height_class}):not(:has(.fs-panel-scroll)) '
            f'[data-testid="stVerticalBlock"] '
            f'{{ min-height: 100% !important; }}'
            "</style>"
        )

    with st.container(border=True, height=container_height):
        header_html = (
            visual_height_css +
            f'<div class="{" ".join(class_names)}">'
            '<div class="fs-panel-header">'
            f'<div><div class="fs-panel-title">{_html(title)}</div>{subtitle_html}</div>'
            f"{action_html}"
            "</div></div>"
        )
        st.markdown(header_html, unsafe_allow_html=True)
        yield


def section_header(number: int, title: str, rule_id: str | None = None) -> None:
    label = f"Section {number:02d}"
    if rule_id:
        label = f"{label} · {rule_id}"
    st.markdown(
        f"""
        <div class="fs-section">
          <div class="fs-section-kicker">{_html(label)}</div>
          <div class="fs-section-title">{_html(title)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def rule_card(rule_id: str, title: str, description: str, status: str = "Passed", severity: str = "INFO") -> None:
    tone = TONE_BY_SEVERITY.get(str(severity).upper(), "default")
    st.markdown(
        f"""
        <div class="fs-rule-card">
          <div class="fs-rule-top">
            <div>
              <div class="fs-rule-id">{_html(rule_id)}</div>
              <div class="fs-panel-subtitle">{_html(title)}</div>
            </div>
            {status_badge(status, tone)}
          </div>
          <div class="fs-rule-description">{_html(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def rule_chip(rule_id: str, title: str = "", status: str = "Passed", severity: str = "INFO") -> None:
    tone = TONE_BY_SEVERITY.get(str(severity).upper(), "default")
    st.markdown(
        f"""
        <div class="fs-rule-chip">
          <div class="fs-rule-chip-main">
            <span class="fs-rule-chip-id">{_html(rule_id)}</span>
            <span class="fs-rule-chip-title">{_html(title)}</span>
          </div>
          {status_badge(status, tone)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(
    category: str,
    fact: str,
    interpretation: str,
    caution: str,
    severity: str = "INFO",
    selected: bool = False,
    compact: bool = False,
) -> None:
    selected_class = " fs-insight-selected" if selected else ""
    tone = TONE_BY_SEVERITY.get(str(severity).upper(), "default")

    if compact:
        st.markdown(
            f"""
            <div class="fs-insight-card fs-insight-compact{selected_class}" data-category="{_html(category)}" data-severity="{_html(severity)}">
              <div class="fs-insight-title">
                <span>{_html(category).title()}</span>
                {status_badge(severity, tone)}
              </div>
              <div class="fs-insight-body">{_html(fact)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="fs-insight-card{selected_class}" data-category="{_html(category)}" data-severity="{_html(severity)}">
          <div class="fs-insight-title">
            <span>{_html(category).title()}</span>
            {status_badge(severity, tone)}
          </div>
          <div class="fs-insight-row fs-insight-row-fact">
            <span class="fs-insight-badge">Fact</span>
            <div class="fs-insight-body">{_html(fact)}</div>
          </div>
          <div class="fs-insight-row fs-insight-row-interpretation">
            <span class="fs-insight-badge">Interpretation</span>
            <div class="fs-insight-body">{_html(interpretation)}</div>
          </div>
          <div class="fs-insight-row fs-insight-row-caution">
            <span class="fs-insight-badge">Caution</span>
            <div class="fs-insight-body">{_html(caution)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, message: str) -> None:
    st.markdown(
        f"""
        <div class="fs-empty-state">
          <div class="fs-empty-title">{_html(title)}</div>
          <div class="fs-empty-message">{_html(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def onboarding_state(title: str, message: str, steps: list[str]) -> None:
    items = "".join(f"<li>{_html(step)}</li>" for step in steps)
    st.markdown(
        f"""
        <div class="fs-empty-state">
          <div class="fs-empty-title">{_html(title)}</div>
          <div class="fs-empty-message">{_html(message)}</div>
          <ul class="fs-empty-message">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
