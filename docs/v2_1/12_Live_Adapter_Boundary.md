# 12. Live Adapter Boundary

> Current status: v2.1 / v4.2 boundary contract.
> This document defines which surfaces may become DB-backed first and which
> surfaces remain deterministic fixture snapshots for visual and product safety.

## 1. Principle

FinSkillOS can use live local DB state without pretending that every cockpit
panel is live. The user should always be able to distinguish:

```text
fixture snapshot
DB-backed live snapshot
partial live state
missing/unavailable state
```

`/api/system-status` owns freshness and completeness. Product tab endpoints
own their own snapshot source.

## 2. Endpoint Boundary

| Endpoint | Current source | Live promotion status | Notes |
|---|---|---|---|
| `/api/system-status` | live when DB reachable | promoted | Reports `dbStatus`, `source`, `dataCompleteness`, `staleFlags`. |
| `/api/system-ops` | fixture catalogue | partial | Protocol runs can be live/NOOP; catalogue remains stable. |
| `/api/control-room` | fixture | deferred | Promote only after a DB-backed aggregate read model exists. |
| `/api/market-kernel` | fixture or live | promoted | Live when DB is reachable; missing ticker bars stay explicit. |
| `/api/analysis-workspace` | fixture | deferred | Requires index/ETF universe freshness contract. |
| `/api/symbol-lab` | fixture | deferred | Requires per-symbol DB fallback and arbitrary ticker policy. |
| `/api/risk-firewall` | fixture or live | promoted first | Live when DB session and account exist; fixture fallback remains explicit. |
| `/api/mission-control` | fixture | deferred | Promote after portfolio snapshot freshness is reliable. |
| `/api/news-intelligence` | fixture/manual POST | deferred | Live polling is not enabled; manual writes may be DB-backed. |
| `/api/event-radar` | fixture/manual POST | deferred | Manual writes may be DB-backed; uncertain statuses stay explicit. |
| `/api/trade-memory` | fixture/manual POST | deferred | Reflection writes may be DB-backed; product view remains fixture-first. |

## 3. Promotion Order

Recommended order:

1. System Ops status and protocol audit evidence.
2. Risk Firewall read model, because guard contracts are explicit. `DONE`.
3. Mission Control, because portfolio snapshots are already operationally central.
4. Market Kernel for stored bars and indicators. `DONE`.
5. Symbol Lab for stored bars, indicators, and arbitrary ticker context.
6. News/Event/Trade Memory read models after manual-write behavior is stable.
7. Control Room last, because it aggregates every other module.

## 3.1 Provider Adapter Status

Market bars have an explicit live provider path through:

```bash
python3 scripts/refresh_market_data.py --adapter yahoo --tickers SPY QQQ TSLA
```

System Ops also exposes `POST /api/system-ops/refresh-market-data`, surfaced as
a protocol card in the React UI. That protocol defaults to offline-safe mock
refresh and can use Yahoo only through explicit environment configuration:

```text
FINSKILLOS_MARKET_REFRESH_ADAPTER=yahoo
FINSKILLOS_MARKET_REFRESH_TICKERS=SPY,QQQ,TSLA
```

These paths write stored bars into the DB through `MarketDataService`. They do
not make `/api/market-kernel` or `/api/symbol-lab` live by themselves. Those
product tabs still need promoted DB-backed read models and missing-data labels
before they should stop returning fixture snapshots.

System Ops also exposes `POST /api/system-ops/calculate-indicators`, surfaced
as a protocol card in the React UI. It computes descriptive indicator snapshots
from stored bars only. No provider call or worker queue is involved.

News remains manual/sample only. A live news adapter requires source,
attribution, rate-limit, and safety-copy rules before promotion.

## 4. UI Rule

Every page must keep source/completeness visible through the global OS status
bar. A tab can show fixture content while system status is live; that is not
a contradiction. It means:

```text
DB is reachable
the product tab still uses deterministic snapshot data
freshness/completeness is reported separately
```

## 5. Test Rule

Until a dedicated live-adapter slice promotes a tab, tests should assert:

- all ten v4.2 GET tabs expose `source`;
- fixture-first tabs return `source=fixture`;
- only `/api/system-status` exposes `dataCompleteness`;
- visual baselines remain deterministic fixture captures.
