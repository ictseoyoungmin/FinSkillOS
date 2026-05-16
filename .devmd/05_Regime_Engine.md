# 05 — Regime Engine

## Goal

Implement the rule-first market regime engine.

## Regime states

```text
PANIC
RECOVERY
HEALTHY_BULL
AGGRESSIVE_RISK_ON
RISK_ON_OVERHEAT
DISTRIBUTION_RISK
DEFENSIVE_TRANSITION
RISK_OFF
```

## Input signals

Use available snapshots:

```text
Fear & Greed
VIX level/change
QQQ RSI
SMH RSI
TSLA RSI
SPY/QQQ trend
sector momentum
breadth proxy when available
DXY/TNX pressure when available
```

MVP may allow manual Fear & Greed/VIX entry if API integration is not ready.

## Output object

```json
{
  "regime": "RISK_ON_OVERHEAT",
  "risk_level": "YELLOW",
  "decision_mode": "HOLD_WINNERS_LIMIT_NEW_ENTRIES",
  "summary": "The market is risk-on, but overheat signals are rising.",
  "positive_factors": [],
  "risk_factors": [],
  "watch_next": []
}
```

## Rule philosophy

Do not use a black-box model for MVP. Use transparent rule-based scoring.

Example:

```text
Risk-on score:
- QQQ above EMA20
- SMH momentum positive
- VIX low or falling
- sector leadership positive

Overheat score:
- Fear & Greed > 75
- QQQ RSI > 70
- SMH RSI > 70
- multiple related sectors crowded
```

## Conflict handling

If momentum and overheat coexist, do not call it a sell signal. Output:

```text
Trend remains constructive, but new chase entries should be limited.
Existing winners can be managed with tighter risk discipline.
```

## Files

```text
finskillos/regime/regime_engine.py
finskillos/regime/regime_rules.py
finskillos/services/regime_service.py
tests/test_regime_engine.py
```

## Acceptance criteria

- Each regime can be reached by a deterministic test fixture.
- Regime history is saved to `market_regimes`.
- The engine returns human-readable factors.
- The output never gives direct buy/sell instructions.
- `RISK_ON_OVERHEAT` handles mixed bullish/overheated states correctly.

## Test commands

```bash
pytest tests/test_regime_engine.py -q
```

## Completion placeholder

```text
Status: TODO
Implemented regimes:
Notes:
Known issues:
```
