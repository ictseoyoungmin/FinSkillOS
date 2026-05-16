# 12 — Trade Journal and Reflection

## Goal

Implement the trade journal and reflection analytics layer.

## Purpose

Trade Journal should help the user discover:

```text
Which regimes produce profits?
Which emotions precede losses?
Which mistake tags are repeated?
Which catalysts work?
Which sectors cause drawdowns?
```

## Journal fields

```text
date
ticker
side
strategy_type
amount
reason
thesis
catalyst
market_regime
emotion_state
result_pnl
result_pnl_pct
r_multiple
mistake_tags
notes
```

## Mistake tags

Seed examples:

```text
Chasing
No Stop
Oversized
Wrong Thesis
Overtrading
Revenge Trade
Early Entry
Late Exit
Ignored Regime
Event FOMO
```

## Reflection views

```text
Performance by regime
Performance by sector/theme
Performance by strategy type
Top positive factors
Top negative factors
Mistake tag frequency
Weekly review
```

## Files

```text
finskillos/services/trade_journal_service.py
finskillos/services/reflection_service.py
finskillos/ui/pages/trade_journal.py
```

## Acceptance criteria

- User can add/edit trade journal entry.
- Entry can capture market regime at trade time.
- Mistake tags are searchable/filterable.
- Reflection summaries are generated from stored trades.
- UI encourages process review, not only P&L.
- Weekly review can be exported or displayed.

## Test commands

```bash
pytest tests/test_trade_journal.py tests/test_reflection_service.py -q
```

## Completion placeholder

```text
Status: TODO
Implemented views:
Notes:
Known issues:
```
