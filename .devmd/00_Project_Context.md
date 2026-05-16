# 00 — Project Context

## Background

FinSkillOS v1 was a competition-oriented dashboard focused on CSV upload, schema inference, metric calculation, visual reports, and auditability.

FinSkillOS v2.1 replaces that direction with a personal trading operating system.

The system is designed around the user's current operating goal:

```text
Current portfolio value: 57,000,000 KRW
Target value: 100,000,000 KRW
Early stop: once 100,000,000 KRW is reached, switch to completion/protection mode
```

The user's current trading style:

```text
- 30,000,000 KRW swing allocation
- 20,000,000 KRW short-term/day-trading allocation
- single-position size should not exceed 10,000,000 KRW
- focused sectors: semiconductors, space, data centers, infrastructure, Tesla/Musk ecosystem
- goal: reach 100,000,000 KRW without a large drawdown event
```

## Product identity

FinSkillOS v2.1 should be treated as:

```text
Decision Support OS ✅
Risk-Aware Operating Mode ✅
Interpretation-First Trading Cockpit ✅
```

Not as:

```text
Buy/Sell Signal Bot ❌
Promised Return System ❌
Generic Chart Dashboard ❌
Automated Investment Adviser ❌
```

## Key UX doctrine

```text
Do not force the user to interpret many charts alone.
Translate signals into state, risk, and next watchpoints.
```

Every analytical surface should answer:

```text
1. What happened?
2. What does it mean?
3. What should I watch next?
```

## Core entities

- Account
- Portfolio snapshot
- Position
- Trade journal entry
- Market bar
- Indicator snapshot
- Market regime
- Risk alert
- Event
- News article
- News impact
- Chart preset
- Sector snapshot
- Interpretation cache

## Core operating loop

```text
Market data updated
→ indicators calculated
→ regime determined
→ guards evaluated
→ interpretation generated
→ command center state updated
→ user reviews action mode
→ trade journal captures decisions
→ weekly reflection improves process
```

## Financial safety requirements

All generated UI text and interpretation must avoid:

- direct transaction commands,
- guaranteed return language,
- personalized investment advice phrased as instruction,
- certainty around market outcomes.

Preferred language:

```text
"Consider limiting new entries."
"Current mode favors existing position management."
"Watch for confirmation."
"Risk is elevated."
```

Avoid:

```text
"Buy TSLA now."
"Sell NVDA tomorrow."
"This will rise."
"Guaranteed setup."
```

## Implementation note

If there is ambiguity between building another feature and keeping the core operating loop understandable, prioritize interpretability and risk control.
