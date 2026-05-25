# 18 — Scheduler / Refresh Policy

Status: `DONE`
Date: `2026-05-25`

## Goal

Define the first operational refresh policy for FinSkillOS without adding
a worker system. The current product target is a local personal investment
OS, so refresh should remain:

```text
manual-first
cron-compatible
script-driven
visible through System Ops and /api/system-status
```

Celery, Redis, and daemon schedulers remain out of scope until the app has
a concrete need for always-on background processing.

## Scope

- Document manual vs scheduled refresh ownership.
- Fill the empty operational scripts:
  - `scripts/refresh_market_data.py`
  - `scripts/calculate_indicators.py`
  - `scripts/run_regime_scan.py`
- Keep all scripts descriptive and idempotent.
- Add lightweight operations tests so the commands keep a valid CLI surface.

## Refresh Contract

```text
market bars      scripts/refresh_market_data.py       manual or after-market cron
indicators       scripts/calculate_indicators.py      after market bars refresh
regime           scripts/run_regime_scan.py           after indicators refresh
risk guards      System Ops protocol                  after portfolio/regime changes
news/events      manual entry / seed protocols        no automatic live refresh yet
visual QA        Docker Playwright gate               before UI completion claims
```

## Product Boundary

Allowed:

- Store market bars.
- Compute indicators.
- Persist descriptive regime snapshots.
- Re-run guard reports and operational protocols.

Not allowed:

- Add brokerage, order, or execution workflows.
- Add automatic trading or price-action commands.
- Add Celery/Redis just to mimic production infrastructure.
- Hide stale data; freshness remains visible through System Ops/status.

## Validation

Executed checks:

```bash
python3 -m pytest tests/test_operations_scripts.py -q  # 5 passed
python3 -m ruff check \
  scripts/refresh_market_data.py \
  scripts/calculate_indicators.py \
  scripts/run_regime_scan.py \
  tests/test_operations_scripts.py                  # passed
python3 scripts/refresh_market_data.py --help       # passed
python3 scripts/calculate_indicators.py --help      # passed
python3 scripts/run_regime_scan.py --help           # passed
```

## Completion

- Scheduler/refresh policy is documented in `docs/v2_1/11_Scheduler_Refresh_Policy.md`.
- Empty refresh scripts are now usable cron-style commands.
- Operations tests cover shell scripts and Python CLI help surfaces.
