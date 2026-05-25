# 15 — System Ops Audit / History Evidence

## Goal

Persist or surface evidence for System Ops protocol runs so operational
actions are reviewable after the fact. This builds on Slice 14:
`/api/system-status`, backup/restore scripts, and verified Docker visual
gates are already complete.

## Product boundary

This slice is about operational evidence only.

Allowed wording:

```text
seed
refresh
recompute
evaluate
protocol
status
result
```

Forbidden scope:

```text
trade execution
brokerage order
buy/sell commands
position mutation from the UI
```

## Proposed contract

Add a protocol-run history read model that records:

```text
protocol key
status: OK / NOOP / ERROR
message
detail
ranAt
dbStatus at run time
source/freshness state if available
durationMs if cheap to capture
```

Initial implementation can be either:

```text
Option A — DB-backed audit table
  Durable and queryable. Preferred once migration scope is acceptable.

Option B — local JSONL operations log
  Lower schema impact. Useful as an interim local-only operational trace.
```

Do not add a broad worker/scheduler system in this slice.

## UI scope

System Ops may add a compact "Recent Protocol Runs" panel, but keep the
v4.2 structure intact:

```text
JudgmentHeader
Drivers
Conflicts
System Health / Freshness Status
DataSourceStrip
Operational Protocols
Recent Protocol Runs
Interpretation
Watchpoints
SafetyCaption
```

The panel must not look like a trading blotter. It is an operations
history.

## Tests

Required focused checks:

```bash
python3 -m pytest \
  tests/test_api_system_ops.py \
  tests/test_api_v42_contract.py \
  tests/test_operations_scripts.py \
  -q

python3 -m ruff check api tests/test_api_system_ops.py
docker compose --profile e2e run --rm e2e npm run build
docker compose --profile e2e run --rm e2e npm run test:visual
```

If a DB migration is added, include:

```bash
python3 -m pytest tests/integration/test_db_migrations.py -q
```

## Completion placeholder

```text
Status: DONE
Chosen storage: local JSONL operations log
Implemented operations:
- Appends each System Ops protocol run to
  `data/logs/system_ops_protocol_runs.jsonl` by default.
- Supports `FINSKILLOS_SYSTEM_OPS_AUDIT_LOG` for test/local override.
- Exposes the latest 5 records via `GET /api/system-ops` as
  `recentProtocolRuns`.
- React System Ops renders `recentProtocolRuns` inside the Operational
  Protocols panel only when records exist, preserving empty-baseline
  layout.
Tests:
- `tests/test_api_system_ops.py`
- `tests/test_api_v42_contract.py`
- Docker frontend build / visual gate
Known issues:
- JSONL is local-node evidence, not a multi-user durable DB audit table.
- A future DB-backed audit table remains useful if System Ops becomes a
  long-running multi-host service.
```
