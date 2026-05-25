# 28 — Symbol Identity / Logo Fallback

Status: `DONE`
Date: `2026-05-25`

## Goal

Give Symbol Lab a stable symbol identity slot so logos/images can be added
later without changing the page contract.

This slice does not fetch official logos. It adds an API/UI contract for
`identity` and renders a local fallback avatar with ticker initials and a
stable brand color.

## Boundary

Allowed:

- Add `identity` metadata to `GET /api/symbol-lab`.
- Render a local fallback avatar in the Symbol Lab technical snapshot.
- Keep `logoUrl` nullable for future provider/cache integration.
- Label fallback identity as `logoSource=local_fallback`.

Not allowed:

- Fetch external logos during page rendering.
- Add unlicensed official logos.
- Make visual baselines depend on external image hosts.
- Add brokerage, order, or execution workflows.

## Runtime Contract

```text
identity: {
  ticker: "SPY",
  name: "S&P 500 ETF",
  logoUrl: null,
  logoSource: "local_fallback",
  avatarText: "SP",
  brandColor: "#0f766e"
}
```

Future logo work can promote `logoSource` to `provider_cache` only after the
provider, attribution, cache, and fallback policies are explicit.

## Validation

Executed checks:

```bash
timeout 60 python3 -m pytest tests/test_api_symbol_lab.py tests/test_api_v42_contract.py -q  # 22 passed
python3 -m ruff check api/schemas/symbol_lab.py api/fixtures/symbol_lab.py api/routes/symbol_lab.py tests/test_api_symbol_lab.py  # passed
docker compose --profile e2e run --rm e2e npm run build  # passed
docker compose up -d --build api web  # passed
curl -s http://localhost:8000/api/symbol-lab?ticker=SPY  # identity.logoSource=local_fallback
docker compose --profile e2e run --rm e2e npm run test:visual  # exit 0; 28 passed, 3 flaky retries passed
```

## Completion

- Symbol Lab API responses include `identity`.
- Fixture, missing, and live DB paths all populate identity metadata.
- React Symbol Lab renders a local fallback avatar beside the ticker.
- Official logo/provider cache remains deferred.
