# 37 — Portfolio Seed Position Coherence

## Status

Completed.

## Intent

Fix the mismatch discovered after Mission Control went live: the sample
account seed can leave a portfolio snapshot with total value while
`positions` remains empty. Live pages then show goal progress but no current
holdings context.

## Scope

- Make the default sample account seed create coherent current positions
  alongside the initial snapshot.
- Repair existing default seed state when it has the original 57M / 7M
  sample snapshot but no positions.
- Keep real imported/user-managed positions untouched.
- Surface position repair/creation details through the existing System Ops
  `seed_sample_account` protocol result.
- Add tests for CLI seed and System Ops behavior.

## Non-Goals

- No broker sync.
- No generic portfolio CSV upload UI.
- No new tables or migrations.

## Acceptance

- A fresh seed creates one account, one initial snapshot, and sample current
  positions whose market value sum plus cash equals the snapshot total.
- Re-running seed is idempotent.
- An existing sample snapshot with no positions is repaired once.
- An existing account with positions is not overwritten.

## Implementation

- `seed_default_account()` now creates five sample positions when it owns the
  baseline seed state.
- Existing default seed rows with the original 57M total / 7M cash snapshot
  and zero positions are repaired on the next seed protocol run.
- Sample position values are scaled from the snapshot investable amount, so
  custom initial total/cash seed arguments remain internally coherent.
- System Ops `seed_sample_account` detail now reports
  `positions_created=<n>` or `positions_reused`.

## Verification

- `python3 -m ruff check finskillos/db/seed.py api/routes/system_ops.py scripts/seed_sample_data.py tests/integration/test_seed_command.py tests/test_api_system_ops.py`
- `timeout 60 python3 -m pytest tests/integration/test_seed_command.py tests/test_api_system_ops.py`
- `docker compose -f docker-compose.yml up -d --build api`
- `curl -s -X POST http://localhost:8000/api/system-ops/seed-sample-account`
- `curl -s http://localhost:8000/api/mission-control`

## Live Repair Result

The existing local DB had `account_reused,snapshot_reused` and no positions.
After running the seed protocol, it returned:

```json
{
  "protocol": "seed_sample_account",
  "status": "OK",
  "detail": "account_reused,snapshot_reused,positions_created=5"
}
```

Mission Control now reports `positionCount=5`, largest position `NVDA`, and
sector/theme exposure maps instead of `Unclassified holdings`.
