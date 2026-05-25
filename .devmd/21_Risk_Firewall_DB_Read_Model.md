# 21 — Risk Firewall DB Read Model

Status: `DONE`
Date: `2026-05-25`

## Goal

Promote the first product tab to a DB-backed read model while preserving
fixture fallback and the v4.2 visual baseline.

Risk Firewall is the first live candidate because it is descriptive,
guard-contract driven, and does not require market/news live adapters.

## Boundary

```text
X-FSO-Use-Fixture: 1     always returns deterministic fixture
DB unavailable           returns deterministic fixture
DB available, no account returns deterministic fixture
DB available, account    returns source=live RiskGuardService snapshot
```

GET `/api/risk-firewall` remains read-only: it evaluates guards with
`persist_alerts=False` and does not mutate positions, alerts, orders, or
brokerage state.

## Live Adapter Note

News and ticker data are not real-time external API-backed yet. Market data
has adapter/service/CLI structure, but the current production-safe adapters
are deterministic mock and CSV. News/event ingestion remains manual/sample.
Live provider adapters need a separate provider slice.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_risk_firewall.py tests/test_api_v42_contract.py -q  # 15 passed
python3 -m ruff check api/routes/risk_firewall.py tests/test_api_risk_firewall.py tests/test_api_v42_contract.py  # passed
docker compose up -d --build api web  # passed
docker compose --profile e2e run --rm e2e npm run test:visual  # 31 passed
```

## Completion

- `/api/risk-firewall` can return `source=live` from DB state.
- Fixture fallback remains explicit and test-covered.
- Visual gate snapshots force fixture product API reads, so live DB state does
  not make screenshot baselines flaky.
- The v4.2 global contract still treats default product tabs as fixture-first
  unless the DB-backed route has a valid live source.
