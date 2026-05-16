# 03 — Portfolio and Goal Tracker

## Goal

Implement the portfolio state and 100,000,000 KRW goal tracking layer.

## User-specific target

```text
Current value baseline: 57,000,000 KRW
Target: 100,000,000 KRW
Remaining: 43,000,000 KRW
Progress: 57%
Early stop: enabled at target achievement
```

## Scope

- Account goal settings.
- Manual portfolio snapshot input.
- Position entry/editing.
- Goal progress calculation.
- Milestone mode calculation.
- Goal completion state.

## Milestone modes

```text
0%–50%     Growth Mode
50%–80%    Balanced Mode
80%–95%    Protection Mode
95%–100%   Completion Guard
>=100%     Challenge Complete
```

## Services

Create:

```text
finskillos/services/portfolio_service.py
finskillos/services/goal_service.py
```

## Core outputs

```json
{
  "current_value": 57000000,
  "target_value": 100000000,
  "progress_pct": 57.0,
  "remaining_value": 43000000,
  "goal_mode": "BALANCED",
  "early_stop_triggered": false
}
```

## UI page

Create a basic Goal Tracker page:

```text
finskillos/ui/pages/goal_tracker.py
```

Required sections:

- current value
- target value
- progress bar
- remaining value
- required return scenarios
- milestone journey
- early-stop explanation

## Acceptance criteria

- User can enter/update current portfolio value.
- Progress percentage is accurate.
- Goal mode changes as value crosses thresholds.
- At 100,000,000 KRW or above, status becomes `CHALLENGE_COMPLETE`.
- UI avoids direct investment instructions.

## Test cases

```text
57M / 100M => 57%, BALANCED
49M / 100M => 49%, GROWTH
85M / 100M => 85%, PROTECTION
96M / 100M => 96%, COMPLETION_GUARD
100M / 100M => 100%, CHALLENGE_COMPLETE
```

## Test commands

```bash
pytest tests/test_goal_service.py -q
```

## Completion placeholder

```text
Status: TODO
Implemented files:
Screens:
Notes:
Known issues:
```
