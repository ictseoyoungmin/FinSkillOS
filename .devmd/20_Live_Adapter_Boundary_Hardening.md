# 20 — Live Adapter Boundary Hardening

Status: `DONE`
Date: `2026-05-25`

## Goal

Harden the fixture/live boundary before adding any DB-backed product tab.
The app should never make fixture fallback look like live data, and live
DB reachability should not imply every tab is DB-backed.

## Boundary Contract

```text
/api/system-status     live DB reachability + dataCompleteness
/api/system-ops        fixture catalogue + live/NOOP protocol runs
all v4.2 GET tabs      fixture-first snapshots until explicitly promoted
manual POST routes     validate input; write only when DB session exists
visual baselines       always deterministic fixture snapshots
```

## Product Rule

`source` means the data origin of that endpoint. It must not be overloaded
with freshness completeness. `/api/system-status` owns freshness with
`dataCompleteness` and `staleFlags`; the other v4.2 product tabs keep
stable read-model snapshots until a dedicated live adapter slice promotes
them one by one.

## Not In Scope

- Implementing live Control Room, Market Kernel, or Symbol Lab adapters.
- Replacing fixture visual baselines.
- Adding broker, order, or execution workflows.
- Adding worker infrastructure.

## Validation

Executed checks:

```bash
python3 -m pytest tests/test_api_v42_contract.py tests/test_api_health.py -q
python3 -m ruff check tests/test_api_v42_contract.py tests/test_api_health.py
```

## Completion

- `docs/v2_1/12_Live_Adapter_Boundary.md` defines the promotion order.
- Cross-tab contract tests pin fixture-first v4.2 GET behavior.
- `/api/system-status` remains the only endpoint with `dataCompleteness`.
