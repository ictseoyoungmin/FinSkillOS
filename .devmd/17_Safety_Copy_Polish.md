# 17 — Safety Copy Polish

Status: `DONE`
Date: `2026-05-25`

## Goal

Polish user-facing safety language so FinSkillOS continues to read as an
Evidence-to-Judgment operating system, not a trading instruction surface.

The target is not only explicit buy/sell wording. This slice also softens
near-instruction phrasing such as:

```text
increase cash
stop aggressive operation
reduce / trim
new entry restriction
take-profit / reduce
```

The replacement vocabulary should stay descriptive:

```text
constraint active
review required
liquidity buffer below floor
exposure-size review
defensive review mode
```

## Scope

- Regime interpretation strings.
- Risk guard titles, messages, and watchpoints.
- Reflection fixture notes that sound like direct hindsight commands.
- Contract tests for soft-action wording in public v4.2 API payloads.

## Not In Scope

- Brokerage, order, or execution features.
- Changing historical database enum values such as legacy trade sides.
- Removing the allowed descriptive market idiom `sell-the-news`.
- Rewriting Korean planning docs that intentionally explain safety policy.

## Implementation Notes

- Replaced Korean action-like phrases in regime and guard outputs with
  constraint/review language.
- Rephrased the Trade Memory fixture note from a direct hindsight command
  into process-review wording.
- Added a cross-tab API safety test that scans public v4.2 payload strings
  for the softened action-like Korean phrases.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_v42_contract.py -q  # 3 passed
timeout 60 python3 -m pytest tests/test_risk_guards.py -q       # 57 passed
python3 -m ruff check \
  finskillos/regime/regime_engine.py \
  finskillos/regime/conflict_resolver.py \
  finskillos/guards/overheat_guard.py \
  finskillos/guards/regime_guard.py \
  finskillos/guards/cash_ratio_guard.py \
  finskillos/guards/drawdown_guard.py \
  finskillos/guards/goal_guard.py \
  tests/test_api_v42_contract.py                                  # passed
docker compose up -d --build api web                              # passed
docker compose --profile e2e run --rm e2e npm run test:visual     # 31 passed
```

## Completion

- User-facing API payloads avoid the targeted soft-action phrases.
- Risk guard unit coverage still passes.
- Public v4.2 contract safety scan covers all ten product tabs.
