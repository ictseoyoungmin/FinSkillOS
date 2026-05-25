# 16 — Fixture / Live / Data-Unavailable Labeling

Status: `DONE`
Date: `2026-05-25`

## Goal

Make the v4.2 cockpit visibly distinguish deterministic fixture data,
DB-backed live data, and unavailable live data without turning any tab into
an execution surface.

This slice uses the global OS status bar as the first implementation point.
Every routed tab already renders that shell, so a single contract-backed
status strip gives the user the same operational context everywhere:

```text
snapshot source
DB status
freshness / stale flags
read-only mode
snapshot timestamp
```

## Product Boundary

Allowed:

- Show whether the cockpit is rendering fixture or live snapshots.
- Show whether the API can reach Postgres.
- Show stale flag counts from `/api/system-status`.
- Preserve the read-only / no-execution product boundary.

Not allowed:

- Add broker, order, or trade execution controls.
- Add live market adapters in this slice.
- Rewrite each tab's evidence hierarchy.
- Hide fixture fallback as if it were live data.

## Implementation Notes

- `OsShell` now queries `/api/system-status` with the existing
  `fetchSystemStatus` fallback contract.
- `OsStatusBar` now renders DB state and freshness state alongside the
  existing snapshot source and read-only caption.
- The status bar includes stable test IDs for the operational source,
  DB state, and freshness state.
- The navigation e2e suite verifies that the global status bar exposes
  fixture/live, DB, freshness, and read-only labels.

## Validation

Executed checks:

```bash
docker compose --profile e2e run --rm e2e npm run build        # passed
docker compose --profile e2e run --rm e2e npm run test:e2e     # 49 passed
docker compose --profile e2e run --rm e2e npm run test:visual  # 31 passed
```

No visual baseline update was required after rebuilding the running web
container.

## Completion

- Global fixture/live/DB/freshness labeling is implemented in the OS shell.
- Structural e2e coverage verifies the operational status strip.
- Docker build, full e2e, and visual validation passed.
