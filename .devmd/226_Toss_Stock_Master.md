# 226 — v4: Toss Stock Master Read (name / market / status / KR flags)

`GET /api/agent/toss/stocks?symbols=` → name, englishName, market, currency,
securityType, status, KR krxTradingSuspended / liquidationTrading. Agent read tool
`read.toss_stocks`. Read-only; available=false when unconfigured. Fixes the
"bare KR code" gap (052790 → 액토즈소프트) at the API level. Frontend display = 229.
Tests: unconfigured, master mapping (incl. liquidationTrading), tool registered.
