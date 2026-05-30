# 12. Live Adapter Boundary

> Current status: v2.1 / v4.2 boundary contract.
> This document defines which surfaces may become DB-backed first and which
> surfaces remain deterministic fixture snapshots for visual and product safety.
> For the precise state vocabulary (fixture / live / live-empty / live-error /
> db-unavailable) and field contract, see `13_State_Vocabulary_And_Data_Source_Contract.md`.
>
> As of Slice 80–83 **all ten product GET tabs are promoted** to DB-backed read
> models; the tables below are kept as the promotion history.

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
| `/api/system-ops` | live/fixture | promoted (partial) | Protocol runs + worker status live; catalogue stable. DB-reachable error still falls back to fixture (open cleanup). |
| `/api/control-room` | live or fixture | promoted | DB-backed operating overview; non-composed rails marked partial in `dataState`. |
| `/api/market-kernel` | live or fixture | promoted | Live when DB is reachable; missing ticker bars stay explicit. |
| `/api/analysis-workspace` | live or fixture | promoted | DB-backed Index Lab read model; coverage levels explicit. |
| `/api/symbol-lab` | live or fixture | promoted | Live when stored bars exist; position/alert context attaches from DB. |
| `/api/risk-firewall` | live or fixture | promoted | Live when DB session and account exist; live-empty/live-error explicit (Slice 80). |
| `/api/mission-control` | live or fixture | promoted | DB-backed goal/portfolio/exposure read model; live-empty/live-error explicit. |
| `/api/news-intelligence` | live or fixture | promoted | DB-backed stored RSS news; manual registration removed; live-error explicit. |
| `/api/event-radar` | live or fixture | promoted | DB-backed read-only event catalog; seeding only via System Ops. |
| `/api/trade-memory` | live or fixture | promoted | DB-backed Slice-12 reflection read model; live-error explicit. |

All tabs honour the `X-FSO-Use-Fixture` override (fixture state) and the offline
`session is None` path (db-unavailable state). See doc 13 §1.

## 3. Promotion Order

This was the recommended order; **all steps are now complete** (Slices 21–66).

1. System Ops status and protocol audit evidence. `DONE`.
2. Risk Firewall read model, because guard contracts are explicit. `DONE`.
3. Mission Control, because portfolio snapshots are already operationally central. `DONE`.
4. Market Kernel for stored bars and indicators. `DONE`.
5. Symbol Lab for stored bars, indicators, and arbitrary ticker context. `DONE`.
6. News / Event / Trade Memory read models after manual-write behaviour is stable. `DONE`.
7. Control Room last, because it aggregates every other module. `DONE`.

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

These paths write stored bars into the DB through `MarketDataService`.
`/api/market-kernel` and `/api/symbol-lab` can read those stored bars without
calling a provider during page rendering. Missing tickers remain explicit
`MISSING` states instead of being filled with fixture bars.

System Ops also exposes `POST /api/system-ops/calculate-indicators`, surfaced
as a protocol card in the React UI. It computes descriptive indicator snapshots
from stored bars only. No provider call or worker queue is involved.

News remains manual/sample only. A live news adapter requires source,
attribution, rate-limit, and safety-copy rules before promotion.

Symbol Lab exposes `identity` metadata with a local fallback avatar. Official
symbol images/logos remain deferred. Promote `identity.logoUrl` to a
provider-backed cache only after provider, attribution, local cache, and
fallback rules are explicit.

Symbol Lab also owns user-managed symbol subscriptions. Arbitrary searched
tickers can be subscribed without editing `FINSKILLOS_MARKET_REFRESH_TICKERS`
or `FINSKILLOS_INDICATOR_REFRESH_TICKERS`. Active subscriptions are added to
System Ops and worker refresh universes. Unsubscribe sets `active=false`; it
does not delete historical bars or indicator snapshots.

## 4. UI Rule

Every page must keep source/completeness visible through the global OS status
bar. With all tabs promoted, the default (no-header) response is **live** when a
DB is reachable. The remaining fixture cases are explicit:

```text
X-FSO-Use-Fixture: 1   -> fixture state (db stays LIVE) — demos / visual baselines
session is None        -> db-unavailable state (db=MISSING) — DB down/unconfigured
```

A live tab with no rows shows live-empty (not fixture); a live read that raises
shows live-error (not fixture). See doc 13 §1 for the full state model.

## 5. Test Rule

The cross-tab contract (`tests/test_api_v42_contract.py`) now reflects the
all-promoted reality:

- all ten v4.2 GET tabs expose `source` and the shared structural contract,
  for **both** fixture and live (no header, DB-state-independent);
- fixture **anchors** (judgment vocabulary + safety category) are pinned with
  the `X-FSO-Use-Fixture` override (deterministic), not the default response;
- every one of the ten tabs honours the fixture override;
- only `/api/system-status` exposes `dataCompleteness`;
- visual baselines remain deterministic fixture captures (forced fixture).

There is no longer a "fixture-first-only" tab list; the previous
`_V42_FIXTURE_FIRST_ENDPOINTS` assumption was removed in Slice 81.
