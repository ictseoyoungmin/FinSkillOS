# 13.8 — React Tabs: Risk Firewall · Mission Control · System Ops

## Goal

Promote three "operational" tabs from the Slice-13.6 placeholder
shell to fully implemented React pages, backed by FastAPI routes
that wrap the existing Python services.

Targeted modules:

```text
- Risk Firewall    (finskillos.services.risk_guard_service)
- Mission Control  (finskillos.services.portfolio_service + GoalService)
- System Ops       (finskillos.db.seed + service-level recompute helpers)
```

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md
.devmd/13_7_React_Market_Analysis_Symbol.md     (precedent for camelCase API + shell pattern)
prototypes/ui/enhanced_dashboard_mockup/finskillos_v4_1_product_cockpit_index.html

finskillos/services/risk_guard_service.py
finskillos/services/portfolio_service.py
finskillos/services/goal_service.py
finskillos/db/seed.py
finskillos/ui/pages/system_ops.py        (current Streamlit page — operational protocol cards)

api/main.py
api/dependencies.py
api/schemas/control_room.py              (GuardSummaryVM template)

frontend/src/pages/risk-firewall/RiskFirewallPage.tsx
frontend/src/pages/mission-control/MissionControlPage.tsx
frontend/src/pages/system-ops/SystemOpsPage.tsx
```

## Scope

Allowed:

```text
- Add FastAPI routes:
    GET  /api/risk-firewall
    GET  /api/mission-control
    GET  /api/system-ops
    POST /api/system-ops/seed-sample-account
    POST /api/system-ops/recompute-regime
    POST /api/system-ops/run-risk-guards
    POST /api/system-ops/seed-sample-events
- Pydantic camelCase schemas mirroring Streamlit page output.
- React pages replacing the three placeholder shells.
- Tests at frontend/e2e/risk-mission-ops.spec.ts.
- Operational action buttons must use safe wording (see below).
```

Not allowed:

```text
- Add execution / brokerage / order endpoints.
- Auto-run destructive operations on page load.
- Surface raw stack traces to the user.
- Touch Market Kernel / Analysis / Symbol (those are 13.7).
- Touch News / Catalyst / Trade Memory (those are 13.9).
```

## Required UI per tab

### Risk Firewall

```text
- Guard result cards (single-position, drawdown, sector
  concentration, cash ratio, regime risk, overheat entry, etc.).
- Active alerts table (date / severity / guard / title / message).
- Risk protocol panel: "Allowed / Limited / Block Add" status with
  a read-only safety explanation.
- Caption: "Read mode — this view never modifies positions".
```

Components:

```text
features/risk-guards/components/GuardResultCard.tsx
features/risk-guards/components/ActiveAlertsTable.tsx
features/risk-guards/components/RiskProtocolPanel.tsx
```

### Mission Control

```text
- Goal tracker hero (current / target / progress / mode badge).
- Milestone timeline (25% / 50% / 75% / 100%).
- Challenge complete + early-stop state callout.
- Portfolio snapshot (total / cash / positions / largest position).
- Sector / theme exposure map.
- "1억 KRW challenge" status caption (the user's domain default).
```

Components:

```text
features/portfolio/components/MissionGoalTracker.tsx
features/portfolio/components/MilestoneTimeline.tsx
features/portfolio/components/CapitalMapPanel.tsx
features/portfolio/components/PortfolioSnapshotPanel.tsx
```

### System Ops

```text
- Protocol cards for:
    - Seed sample account
    - Recompute Market Regime
    - Run Risk Guards
    - Seed sample events
- Each card surfaces: protocol name, what it does, idempotency note,
  last-run timestamp.
- Confirm dialog before any destructive-looking protocol — the
  cleanup contract explicitly forbids running these silently.
- Caption: "Operational protocols only — no trading actions."
- DB / migration / data-source status pills (LIVE / FIXTURE).
```

Safe button wording:

```text
- "Run protocol"
- "Seed sample data"
- "Recompute interpretation"
- "Refresh stored view"
```

Forbidden wording (do NOT add):

```text
- "Execute trade"
- "Place order"
- "Buy"
- "Sell"
- "Run order"
```

## Required tests

```text
frontend/e2e/risk-mission-ops.spec.ts
```

Assertions:

```text
- /risk-firewall renders guard cards and the active alerts table.
- /mission-control renders the goal tracker + milestone timeline.
- /system-ops renders protocol cards and the operational caption.
- No execution captions appear on any route (Buy / Sell / Execute /
  Trade Now / Order / Place Order / 지금 사라 / 지금 팔아라 /
  매수 버튼 / 매도 버튼).
- POST /api/system-ops/* endpoints respond 200 with structured
  status JSON (no HTML, no raw stack traces).
```

Backend:

```text
tests/test_api_risk_firewall.py
tests/test_api_mission_control.py
tests/test_api_system_ops.py            (covers GET + POST protocols)
```

## Verification commands

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q
python3 -m ruff check finskillos api tests

cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e

docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e
```

## Completion placeholder

```text
Status: TODO
Implemented routes:
Implemented React pages:
Operational protocols:
Tests added:
Notes:
Known issues:
```

## Stop condition

Stop after 13.8. Do not start 13.9 / 13.10 unless the user
explicitly asks.
