# 13 — Testing and Acceptance Criteria

## Goal

Define project-level quality gates for FinSkillOS v2.1.

## Test categories

```text
1. DB and migration tests
2. Repository tests
3. Service tests
4. Signal calculation tests
5. Regime rule tests
6. Risk guard tests
7. UI smoke tests
8. Safety language tests
9. Performance budget checks
```

## Minimum acceptance tests

### DB

```text
- migrations run from empty database
- seed account created
- portfolio snapshot uniqueness enforced
- JSONB alert payload stored/read
```

### Portfolio / Goal

```text
- 57M/100M = 57%
- 100M/100M triggers challenge complete
- milestone mode changes correctly
```

### Market signals

```text
- RSI calculation matches known fixture
- EMA calculation matches known fixture
- Bollinger bands calculated
- duplicate market bars ignored
```

### Regime engine

```text
- risk-on fixture returns AGGRESSIVE_RISK_ON
- overheat fixture returns RISK_ON_OVERHEAT
- panic fixture returns PANIC
- mixed signal fixture returns conflict interpretation
```

### Risk guards

```text
- position > 10M KRW triggers alert
- drawdown > 8% triggers yellow
- drawdown > 15% triggers defensive
- sector concentration triggers warning
```

### UI smoke

```text
- Command Center renders with seed data
- Goal Tracker renders with seed data
- Research Hub loads lazily
- Event Radar renders events
- Trade Journal renders empty state
```

### Safety language

Automated checks should fail for direct command phrases such as:

```text
"buy now"
"sell now"
"guaranteed"
"must buy"
"will rise"
```

Korean equivalents should also be guarded:

```text
"지금 매수"
"무조건 상승"
"보장"
"반드시 사"
"오늘 팔아"
```

## Performance budget

```text
Command Center initial render: < 1.5s with cached snapshot
Portfolio risk refresh: < 500ms
Regime calculation: < 300ms
Signal update for 20 tickers: < 3s
Full market data refresh: < 15s
```

## Required CI command

```bash
python -m compileall app.py finskillos
pytest tests -q
```

## Completion placeholder

```text
Status: TODO
Implemented tests:
Coverage notes:
Known gaps:
```
