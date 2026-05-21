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

v4.1 visual shell baseline:
prototypes/ui/enhanced_dashboard_mockup/index.html

v4.2 Evidence-to-Judgment UX baseline:
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html

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

## Completion note

```text
Status: DONE_AS_REACT_RISK_MISSION_OPS_V0 (2026-05-21)

Implemented routes:
- GET  /api/risk-firewall  — fixture-first guard cards (8 entries) +
  active alerts table (date / severity / guard / title / message) +
  Allowed / Limited / Block Add protocol panel.
- GET  /api/mission-control — fixture-first goal tracker (current /
  target / remaining / progress / mode / phase / challenge label) +
  4-step milestone timeline + portfolio snapshot + sector / theme
  capital map + challenge status caption.
- GET  /api/system-ops — fixture-first protocol catalog (4 safe
  protocols) + LIVE / FIXTURE data-source pills.
- POST /api/system-ops/seed-sample-account
- POST /api/system-ops/recompute-regime
- POST /api/system-ops/run-risk-guards
- POST /api/system-ops/seed-sample-events
  All four POST handlers respond with a structured
  ProtocolRunResult JSON (status / message / detail / ranAt). When
  no DB session is available (fixture-first shell) the handler
  returns status=NOOP instead of raising. Internal exceptions are
  converted to status=ERROR with the exception class name in
  `detail` — never a raw stack trace, never HTML.

Implemented Pydantic schemas:
- api/schemas/risk_firewall.py (RiskFirewallResponse, ActiveAlertItem,
  RiskProtocolEntry) — re-uses GuardSummaryVM from Control Room.
- api/schemas/mission_control.py (MissionControlResponse, GoalTracker,
  MilestoneItem, PortfolioSnapshotPanel, CapitalMapSlice)
- api/schemas/system_ops.py (SystemOpsResponse, ProtocolCard,
  DataSourcePill, ProtocolRunResult)

Implemented fixtures (api/fixtures/):
- risk_firewall.py — 8 guards, 3 active alerts, 3-row protocol panel.
- mission_control.py — 73.4% progress fixture aligned with Control
  Room (Phase 3 / 5, TSLA above single-position limit, 1억 KRW
  challenge label, sector + theme exposure rows).
- system_ops.py — 4 protocol cards with safe wording + 4 data-source
  pills (DB / Market Bars / News + Event stores / Mode).

Implemented React feature modules:
- features/risk-guards/{api,types}.ts + components/
  (GuardResultCard, ActiveAlertsTable, RiskProtocolPanel — GuardCard
  re-used from Slice 13.6).
- features/portfolio/{api,types}.ts extended with Mission Control
  models + new components (MissionGoalTracker, MilestoneTimeline,
  PortfolioSnapshotPanel, CapitalMapPanel).
- features/system-ops/{api,types}.ts + components/
  (ProtocolCardItem with inline confirm dialog + status pill,
  DataSourceStrip). runSystemOpsProtocol(...) calls the POST routes
  via fetch and returns the typed ProtocolRunResult.

Implemented React pages (replaced PlaceholderPage shells):
- pages/risk-firewall/RiskFirewallPage.tsx — three-column grid
  (Guard Results · Active Alerts · Risk Protocol) with a
  "Read mode — this view never modifies positions" caption.
- pages/mission-control/MissionControlPage.tsx — two-column grid
  (Goal Tracker + Milestones · Portfolio Snapshot + Capital Map),
  early-stop callout when triggered, challenge status caption
  pinned to the page footer.
- pages/system-ops/SystemOpsPage.tsx — top LIVE / FIXTURE strip +
  protocol cards in a responsive grid + safety caption
  "Operational protocols only — no trading actions."

Safe button wording (forbidden vocabulary not used anywhere):
- "Run protocol", "Seed sample data", "Recompute interpretation",
  "Refresh stored view". Confirm dialog gates every protocol run
  and quotes the idempotency note back to the user.

Frontend mock fixtures (shared/mocks/fixtures/):
- riskFirewall.fixture.ts
- missionControl.fixture.ts
- systemOps.fixture.ts
  All three twin the Python fixtures so React Query falls back to
  the deterministic baseline when the FastAPI container is offline.

Tests added:
- tests/test_api_risk_firewall.py (7 cases)
- tests/test_api_mission_control.py (8 cases)
- tests/test_api_system_ops.py (8 cases — covers GET + every POST
  endpoint, asserts structured JSON / no HTML / no stack-trace
  markers / no forbidden wording).
- frontend/e2e/risk-mission-ops.spec.ts (5 specs).
- frontend/e2e/navigation.spec.ts updated to drop the three
  promoted routes from the placeholder list (only News Intel /
  Catalyst Watch / Trade Memory remain on the EmptyState shell).

Verification:
- python3 -m compileall app.py finskillos api scripts   → clean
- python3 -m ruff check finskillos api tests            → All checks passed
- python3 -m pytest tests                               → 564 passed
- npx tsc -b                                            → exit 0 (clean)
- npm run lint                                          → 0 errors,
                                                          1 pre-existing
                                                          react-refresh
                                                          warning carried
                                                          from Slice 13.6.
- npm run build / npm run test:e2e                      → run inside the
                                                          Docker `web`
                                                          (node:20-alpine)
                                                          + `e2e`
                                                          (mcr.microsoft.com/
                                                          playwright:v1.49.1-
                                                          noble) containers.
                                                          Local WSL node is
                                                          v16; Vite 5 needs
                                                          Node 18+.

Notes:
- Routes stay fixture-first per the api/dependencies.py TODO. POST
  protocols use the same session_scope helper; when no DB session
  exists they return status=NOOP rather than 500ing.
- GuardCard component from Slice 13.6 is reused by Risk Firewall,
  so the status glyph / pill semantics stay consistent across
  Control Room and Risk Firewall.
- Forbidden-execution-label scan covers the three new routes via
  the Slice 13.8 e2e spec; descriptive-only output rule preserved.
- Streamlit Slice 07 / system_ops debug page remains untouched.

Known issues:
- npm run build / npm run test:e2e cannot run on the WSL bash that
  ships Node 16 — same environment limitation Slice 13.6 / 13.7
  flagged. Use the docker-compose profiles documented in Slice 13.6
  cleanup §3.
- POST protocols always return NOOP in fixture-first mode (no DB).
  Live integration requires the explicit error-surface contract
  from .devmd/13_6 cleanup §6.
- Mission Control "Capital Map" + "Theme Map" are simple bar lists.
  The v4.1 mockup's bar canvas is deferred until the shared chart
  primitive lands in Slice 13.10 visual QA.
- Mission Control fixture goal-mode is BALANCED (matches 0.73
  ratio per goal_tracker.goal_mode_for), while the Control Room
  Slice 13.6 fixture pins COMPLETION_GUARD as decorative copy.
  When the live wire-up lands both pages will share the goal-mode
  value derived from goal_tracker.calculate_goal_status.
```

## Stop condition

Stop after 13.8. Do not start 13.9 / 13.10 unless the user
explicitly asks.

## Post-Slice-13.8 Cleanup

```text
13.8 Cleanup Status: DONE_AS_REACT_RISK_MISSION_OPS_CLEANUP_V0 (2026-05-21)

Cleanup implemented:
- Aligned Playwright e2e Docker image with @playwright/test version.
  frontend/Dockerfile.e2e:
    mcr.microsoft.com/playwright:v1.49.1-noble
    → mcr.microsoft.com/playwright:v1.60.0-noble
- Softened Risk Firewall limited protocol wording from advisory action
  to constraint-state wording.
  api/fixtures/risk_firewall.py + frontend/src/mocks/fixtures/
    riskFirewall.fixture.ts now use:
    "Exposure-size review remains required while concentration or
     overheat flags remain active."
  (replaces "Consider reducing exposure size.")
- Normalized prototype path references across slice 13.7 / 13.8 /
  13.9 / 13.10 devmd Read-first sections:
    v4.1 shell baseline:
      prototypes/ui/enhanced_dashboard_mockup/index.html
    v4.2 Evidence-to-Judgment baseline:
      prototypes/ui/enhanced_dashboard_mockup/v4_2/
        finskillos_v4_2_evidence_judgment_mockup.html
- Updated frontend package metadata to Slice 13.8:
    frontend/package.json: version 0.13.8 + Slice-13.8 description.
    frontend/package-lock.json: root package version bumped to 0.13.8
    (lockfile metadata only — no dependency version changes).
- Updated .devmd/13_9 instructions to use the v4.2
  Evidence-to-Judgment UX direction. Each tab now reads as
  Judgment Header → Primary Drivers → Conflicts / Uncertainty →
  Evidence Details → Integrated Interpretation → Watchpoints, with
  per-tab judgment vocab (Narrative / Event Exposure / Process)
  and the matching v4.2 component list.

Remaining:
- 13.9 still not implemented.
- 13.7 / 13.8 pages are functionally complete but not refactored
  into the v4.2 Judgment Header structure — that is the 13.10
  visual-parity / refactor job.
- Full screenshot parity remains deferred to 13.10.
```
