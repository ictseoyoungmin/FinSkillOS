# 30 — Yahoo Provider Diagnostics and Symbol Chart

Status: `DONE`
Date: `2026-05-25`

## Goal

Tighten the Symbol Lab arbitrary-search flow after provider research:

- Treat Yahoo Finance as an unofficial chart endpoint that returns OHLCV
  arrays under `chart.result[0].timestamp` and
  `chart.result[0].indicators.quote[0]`.
- Make provider-preview failures visible in the Symbol Lab missing-data hint.
- Keep the recent bars table newest-first.
- Add a chart view for Symbol Lab so the user is not limited to text/table
  evidence.

## Boundary

Allowed:

- Use the existing dependency-free `LineChart` shared component.
- Keep API/provider calls out of React. The page reads the API snapshot only.
- Let arbitrary searched symbols show provider-preview bars when the DB has no
  stored bars and `FINSKILLOS_SYMBOL_PREVIEW_ADAPTER` is enabled.
- Label preview evidence as preview/snapshot evidence, not stored DB evidence.

Deferred:

- Foldered subscription groups similar to Toss watchlists. This needs a
  separate DB/API/UI slice because folders require durable folder rows,
  membership changes, and filtered views.

Not allowed:

- Add execution/order/trade controls.
- Treat Yahoo preview data as a streaming quote feed.
- Persist preview rows during page render.

## Yahoo Finance Note

The current adapter uses the commonly observed unofficial endpoint:

```text
GET https://query1.finance.yahoo.com/v8/finance/chart/{symbol}
```

The response is not a single `bars` field. Bars are reconstructed by aligning:

- `chart.result[0].timestamp[]`
- `chart.result[0].indicators.quote[0].open[]`
- `chart.result[0].indicators.quote[0].high[]`
- `chart.result[0].indicators.quote[0].low[]`
- `chart.result[0].indicators.quote[0].close[]`
- `chart.result[0].indicators.quote[0].volume[]`

Because this endpoint is unofficial, provider errors remain non-fatal and are
reported as setup/watchpoint context.

## Validation

Executed checks:

```bash
python3 -m ruff check api/routes/symbol_lab.py
timeout 60 python3 -m pytest tests/test_api_symbol_lab.py tests/test_api_v42_contract.py -q  # 23 passed
docker compose up -d --build api web  # passed; Vite production build passed inside Docker
docker compose --profile e2e run --rm e2e npm run test:visual  # 25 passed, 6 prototype-layout timeouts
git diff --check  # passed
```

Visual note:

- `symbol-lab` structural contract passed.
- `symbol-lab` screenshot baseline passed.
- `symbol-lab` prototype-layout comparison passed.
- Full visual gate still failed on unrelated prototype-layout timeout cases:
  control-room, market-kernel, risk-firewall, mission-control, trade-memory,
  and system-ops.

## Completion

- Symbol Lab table displays recent bars newest-first.
- Symbol Lab renders a close-line chart from API-provided bars.
- Provider preview evidence no longer presents itself as stored DB-only data.
- Provider preview failures appear in missing-data setup guidance.
