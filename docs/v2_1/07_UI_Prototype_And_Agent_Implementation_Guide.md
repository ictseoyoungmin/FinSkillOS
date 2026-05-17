# 07 — UI Prototype and Agent Implementation Guide

## Purpose

This document tells implementation agents which UI prototype is authoritative and how to translate the prototype into the Streamlit / application implementation.

## Latest UI Source of Truth

- `prototypes/ui/os_style_mockup/index.html`

This file is the latest v3.3 OS-style multi-tab mockup.

It includes:
- Control Room
- Market Kernel
- Risk Firewall
- Mission Control
- Catalyst Watch
- Analysis Workspace
- Trade Memory
- System Ops
- Dark / Light / Studio theme switching
- U.S.-market-focused symbol search and watchlist-driven chart switching

## UI Naming Rules

Use the current OS naming only:

| Current name | Deprecated names to avoid |
| --- | --- |
| Control Room | Command Center |
| Market Kernel | Market Regime |
| Risk Firewall | Portfolio Risk |
| Catalyst Watch | Event Radar |
| Mission Control | Goal Tracker |
| Analysis Workspace | Research Hub |
| Trade Memory | Trade Journal |
| System Ops | Settings / Data |

## Implementation Priority

1. Preserve the OS mental model.
2. Prioritize interpretation and risk context over raw chart density.
3. Keep the searchable symbol chart as the Control Room visual anchor.
4. Keep U.S. market focus for the main mockup.
5. Do not produce direct buy/sell recommendations.
6. Render risk, constraints, watchpoints, and reflection support.

## Streamlit Translation Guidance

The HTML prototype is a visual and interaction reference, not a requirement to duplicate all CSS exactly.

When translating to Streamlit:
- Use tabs/pages matching the OS navigation.
- Keep the Control Room dense but readable.
- Maintain the Market Kernel / Risk Firewall / Mission Control semantic separation.
- Use cached snapshots for initial rendering.
- Do not block implementation on pixel-perfect styling.
