# 06 — Risk Guards

## Goal

Implement portfolio and behavior risk guards.

## Required guards

```text
DrawdownGuard
SinglePositionLimitGuard
SectorConcentrationGuard
CashRatioGuard
OverheatEntryGuard
EventRiskGuard
GoalProtectionGuard
OvertradingGuard
```

## User-specific hard rule

```text
Single position should not exceed 10,000,000 KRW.
```

This should be implemented as a configurable value, defaulting to 10,000,000 KRW.

## Alert levels

```text
INFO
YELLOW
RED
```

## Drawdown guard

```text
From peak:
-8%  => Yellow Alert
-10% => Risk Reduction Mode
-15% => Defensive Mode
```

## Goal protection guard

```text
>=80% goal progress: increase protection warnings
>=95% goal progress: completion guard
>=100%: challenge complete / early stop
```

## Guard output schema

```json
{
  "guard_name": "SinglePositionLimitGuard",
  "severity": "YELLOW",
  "title": "Single position limit approaching",
  "message": "TSLA is approaching the 10,000,000 KRW position limit.",
  "payload": {
    "ticker": "TSLA",
    "market_value": 9500000,
    "limit": 10000000
  }
}
```

## Files

```text
finskillos/guards/base.py
finskillos/guards/drawdown_guard.py
finskillos/guards/concentration_guard.py
finskillos/guards/cash_guard.py
finskillos/guards/overheat_guard.py
finskillos/guards/event_risk_guard.py
finskillos/guards/goal_guard.py
finskillos/services/risk_guard_service.py
```

## Acceptance criteria

- Guards run from current portfolio snapshot without expensive full-history queries.
- Alerts are persisted to `alerts`.
- Guard results are visible in Command Center and Portfolio Risk.
- Single-position guard works with KRW absolute value.
- Drawdown guard works from stored portfolio peak.
- No guard emits direct transaction instructions.

## Test commands

```bash
pytest tests/test_risk_guards.py -q
```

## Completion placeholder

```text
Status: TODO
Implemented guards:
Notes:
Known issues:
```
