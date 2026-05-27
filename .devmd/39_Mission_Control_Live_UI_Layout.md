# 39 — Mission Control Live UI Layout

## Status

Done.

## Intent

Rework Mission Control after the page became DB-backed. The previous layout
was fixture-shaped: large judgment/drivers/conflicts blocks dominated the
first viewport. Live Mission Control should instead foreground goal progress,
portfolio state, guard count, source/freshness, and exposure context.

## Scope

- Make the first viewport operationally dense and scannable.
- Keep judgment copy visible but compact.
- Move evidence/detail panels below the mission and portfolio state.
- Avoid adding new data contracts.
- Keep existing tests/test ids stable where practical.

## Non-Goals

- No backend API changes.
- No charting work.
- No direct-action controls.

## Completed

- Replaced the old fixture-shaped topline with a compact operational command row.
- Put narrative judgment, live source/portfolio status, and goal progress in the first scan band.
- Moved portfolio snapshot, milestones, and exposure maps into the second band.
- Moved drivers/conflicts/interpretation/watchpoints below the live mission state.
- Removed the duplicate safety caption rendering from the page footer.

## Verification

- `python3 -m ruff check .`
- `timeout 180 env FINSKILLOS_SKIP_DOTENV=1 python3 -m pytest tests -q`
- `docker compose -f docker-compose.yml exec -T web npm run build`
- `docker compose -f docker-compose.yml up -d --build web`
