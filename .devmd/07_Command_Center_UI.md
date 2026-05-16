# 07 — Command Center UI

## Goal

Implement the primary cockpit screen for FinSkillOS v2.1.

## UX priority

The first screen should immediately answer:

```text
What is the current state?
What is the risk?
What mode should I operate in today?
What should I watch next?
```

## Required sections

```text
Market State Banner
Goal Progress
Portfolio Value
Decision Mode
Key Risk Alerts
AI/Template Interpretation
Suggested Action Mode
Portfolio Overview
Cash / Buying Power
```

## Data source

The page should read a compact state snapshot first:

```text
current account state
latest portfolio snapshot
latest market regime
latest risk alerts
latest goal status
```

Avoid heavy chart rendering on first load.

## UI wording examples

Good:

```text
"Risk-On / Overheat Warning"
"Momentum is strong but crowded."
"Existing winner management is favored over aggressive new chase entries."
"Watch breadth and VIX for deterioration."
```

Avoid:

```text
"Buy now."
"Sell today."
"This will go up."
```

## Files

```text
finskillos/ui/pages/command_center.py
finskillos/ui/components/state_banner.py
finskillos/ui/components/metric_card.py
finskillos/ui/components/alert_card.py
finskillos/ui/components/interpreter_panel.py
```

## Acceptance criteria

- Initial render does not trigger full market data refresh.
- Page shows goal progress, regime, risk alerts, and interpretation.
- Empty-state UI exists if there is no portfolio data.
- Safety language is used consistently.
- Page renders with sample seed data.

## Test commands

```bash
pytest tests/test_ui_command_center.py -q
streamlit run app.py
```

## Completion placeholder

```text
Status: TODO
Implemented components:
Screenshots:
Notes:
Known issues:
```
