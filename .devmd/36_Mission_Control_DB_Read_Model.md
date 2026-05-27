# 36 — Mission Control DB Read Model

## Status

Completed.

## Intent

Promote Mission Control from a fixture-only page into a DB-backed mission
read model that connects the user's stored account, latest portfolio
snapshot, current holdings, goal progress, exposure map, milestones, and
active guard context.

## Scope

- Keep `X-FSO-Use-Fixture: 1` as the deterministic fixture override.
- Read the default account from `FINSKILLOS_DEFAULT_ACCOUNT_NAME`, falling
  back to the first stored account when needed.
- Build the live Mission Control payload from:
  - `GoalService`
  - `PortfolioService`
  - `AccountRepository`
  - `AlertRepository`
- Populate goal progress, phase, milestones, portfolio snapshot panel,
  sector capital map, theme map, evidence drivers, conflicts, watchpoints,
  and integrated interpretation from the same stored account.
- Return a live empty-state payload when the DB is reachable but no account
  exists.
- Fall back to the existing fixture when the DB session is unavailable.

## Notes

- No new table or migration was required; this slice composes the existing
  account, portfolio snapshot, position, and alert data.
- The route remains read-only and does not call external providers during
  page rendering.
- `largestPositionWeightPct` is now a true display percent in the live
  payload, derived from the existing ratio returned by `PortfolioService`.
- Capital-map tones are descriptive concentration labels only:
  `danger >= 35%`, `warning >= 20%`, `neutral <= 5%`, otherwise `info`.

## Verification

- `python3 -m ruff check api/routes/mission_control.py tests/test_api_mission_control.py tests/test_api_v42_contract.py`
- `timeout 60 python3 -m pytest tests/test_api_mission_control.py`
- `timeout 90 env FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests/test_api_v42_contract.py`

## Follow-Up Candidates

- Mission Control UI layout can now be redesigned against live data instead
  of fixture composition.
- Durable System Ops audit table remains useful so Mission Control can show
  latest refresh/protocol status directly beside goal state.
