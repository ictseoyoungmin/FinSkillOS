# 13.11 — React UI Completion Audit + v4.2 Parity Polish

## Goal

Bring **every** React tab to the v4.2 Evidence-to-Judgment hierarchy,
not just the Slice 13.9 surface (News / Catalyst / Trade Memory). Then
make the Playwright structural suite *enforce* that hierarchy per tab,
so a missing panel breaks CI even before a screenshot baseline is
compared.

This slice exists because Slice 13.10 was downgraded to `PARTIAL_AS_
QA_SCAFFOLD_ONLY` — the visual baseline was wrapped around an
incomplete UI. Do not reopen 13.10. Treat its all-tabs spec as
scaffolding that 13.11 hardens.

## Read first

```text
.devmd/13_6_Frontend_Migration_Shell.md
.devmd/13_7_React_Market_Analysis_Symbol.md
.devmd/13_8_React_Risk_Mission_Ops.md
.devmd/13_9_React_News_Events_TradeMemory.md     (already v4.2)
.devmd/13_10_React_Prototype_Parity_Visual_QA.md (PARTIAL)

prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
prototypes/ui/enhanced_dashboard_mockup/v4_2/screenshots/
  01_control_room.png         02_market_kernel.png
  03_analysis_workspace.png   04_symbol_lab.png
  05_risk_firewall.png        06_mission_control.png
  07_news_intelligence.png    08_catalyst_watch.png
  09_trade_memory.png         10_system_ops.png

frontend/src/shared/ui/EvidencePanels.tsx        (existing DriversPanel /
                                                  ConflictsPanel /
                                                  InterpretationPanel /
                                                  WatchpointsPanel)
frontend/src/features/news/components/NewsJudgmentHeader.tsx
frontend/src/features/events/components/EventExposureJudgment.tsx
frontend/src/features/trades/components/ProcessJudgmentHeader.tsx
```

## Scope

Allowed:

```text
- Add a shared <JudgmentHeader /> component in frontend/src/shared/ui
  that supersedes the per-feature JudgmentHeader copies. The 13.9
  feature variants either re-export it or stay as thin wrappers.
- Add a <SafetyCaption /> testid'd component used uniformly.
- Add v4.2 hierarchy + required testids to the 7 tabs that lack it
  (Control / Market Kernel / Analysis / Symbol / Risk Firewall /
  Mission / System Ops).
- Add v4.2 vocabulary fields (`judgment`, `drivers`, `conflicts`,
  `watchpoints`, `interpretation`, `safetyCaption`) to the matching
  API response schemas + fixtures + Python pydantic models.
- Rewrite frontend/e2e/visual/all-tabs.visual.spec.ts so each route
  asserts its 5–6 required evidence testids — not just the page root.
- Bootstrap and commit screenshot baselines under
  frontend/e2e/visual/all-tabs.visual.spec.ts-snapshots/.
- Update README §9 / frontend/e2e/visual/README.md if testid names or
  npm scripts change.
```

Not allowed:

```text
- Add execution / brokerage / order endpoints.
- Add live news / event / market data adapters.
- Change Streamlit Slice 07 debug UI.
- Touch backend services (NewsService / EventService /
  TradeJournalService / RiskGuardService / RegimeService etc.) —
  this slice is UI + schema + fixture work only.
- Re-introduce Slice 13.10 baseline-bootstrap-from-host workflow —
  PNGs must come from the docker e2e profile.
- Demand pixel-perfect parity with the static HTML mockup. The
  Judgment Header text must MATCH the mockup vocabulary, but
  typography weight / spacing parity remains tolerated under the
  0.03 maxDiffPixelRatio.
```

## v4.2 Evidence-to-Judgment hierarchy (shared by every tab)

Every tab must render, in this exact order:

```text
1. JudgmentHeader
     - eyebrow      (per-tab vocabulary, see "Per-tab vocabulary" below)
     - title        (verdict noun phrase, accent on the qualifier)
     - confidence   (0–100; tag colour green/amber/red by threshold)
     - summary      (1–2 line narrative)
2. PrimaryDriversPanel
     - 3 driver cards (score / title / note)
3. ConflictsPanel
     - 1–3 conflict cards (title / note)
4. EvidencePanels (tab-specific, see "Per-tab required testids")
     - left column   — evidence inputs
     - center column — synthesis (chart / table / impact map / matrix)
     - right column  — judgment output + mini list of review conditions
5. InterpretationPanel
     - Integrated Interpretation block (verdict re-state in product
       voice + "why it matters" + "what remains uncertain")
6. WatchpointsPanel
     - 2–4 watchpoints (title / note)
7. SafetyCaption
     - "Judgment, not execution instruction" anchor caption per tab.
       Wording must match the per-tab safety caption defined in the
       existing API schemas (event-radar already pins
       "preparation / exposure score only … not a price direction
       prediction.").
```

## Per-tab vocabulary

Pin these exactly so the structural tests can match them.

```text
Tab               eyebrow                        judgment title accent     safety caption category
control           GLOBAL OPERATING VERDICT       Risk-On but Extended      Global operating posture (not execution)
kernel            TECHNICAL SIGNAL JUDGMENT      Constructive Tape         Technical interpretation (not entry signal)
                                                 with Overheat Risk
analysis          MARKET STRUCTURE JUDGMENT      Leadership is Narrow      Structural breadth read (not allocation call)
symbol            SYMBOL JUDGMENT · <TICKER>     Recovering but            Symbol interpretation (not trade signal)
                                                 Constrained
firewall          RISK PERMISSION JUDGMENT       Limited Risk Mode         Read-only — this view never modifies positions
mission           MISSION RISK JUDGMENT          Progress Strong,          Goal interpretation (not return forecast)
                                                 Risk Budget Narrows
news              NARRATIVE JUDGMENT             AI Narrative Strong,      Descriptive narrative view only (no advice)
                                                 Volatility Risk Elevated
catalyst          EVENT EXPOSURE JUDGMENT        Event Cluster High        Event risk score = preparation / exposure
                                                                           score only … not a price direction prediction.
memory            PROCESS JUDGMENT               Profits in Risk-On,       Reflection / process review (no execution)
                                                 Losses in FOMO
ops               SYSTEM TRUST JUDGMENT          Local System Usable       Operational protocols only — no trading actions
                                                 with Partial Data
```

The exact title strings are templates — fixtures may substitute
deterministic values, but the eyebrow + safety-caption category must be
verbatim (the e2e spec asserts substrings).

## Per-tab required testids

Each route must expose all of these. Pick the closest existing
component; if none exists, add a new one that wraps the existing data
in a v4.2 evidence-card.

```text
Control Room (/)
  - control-room-grid
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - operating-state-hero
  - portfolio-market-tape
  - risk-firewall-summary     (the Control-Room compact guard stack;
                              existing testid from Slice 13.6)
  - catalyst-watch-summary
  - watchlist-card
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Market Kernel (/market-kernel)
  - market-kernel-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - symbol-universe-rail
  - ticker-search
  - chart-panel
  - indicator-snapshot
  - market-interpretation
  - watchpoints-panel
  - safety-caption

Analysis Workspace (/analysis-workspace)
  - analysis-workspace-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - index-universe-table
  - relative-strength-ranking
  - tape-strength-cards
  - regime-context
  - missing-data-panel
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Symbol Lab (/symbol-lab)
  - symbol-lab-page
  - judgment-header               (title carries the resolved ticker)
  - drivers-panel
  - conflicts-panel
  - symbol-search
  - position-context
  - technical-snapshot
  - ticker-news
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Risk Firewall (/risk-firewall)
  - risk-firewall-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - guard-result-cards
  - active-alerts
  - risk-protocol-panel
  - protocol-matrix-explanation   (Allowed / Limited / Blocked)
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Mission Control (/mission-control)
  - mission-control-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - goal-tracker
  - milestone-timeline
  - capital-map
  - portfolio-snapshot
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

News Intelligence (/news-intel)        — already partial v4.2; pin testids
  - news-intelligence-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - holdings-relevant-news
  - news-impact-map
  - event-linked-news
  - manual-article-entry
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Catalyst Watch (/catalyst-watch)       — already partial v4.2; pin testids
  - catalyst-watch-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - event-risk-table
  - date-status-badges
  - event-score-drivers
  - manual-event-entry
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

Trade Memory (/trade-memory)           — already partial v4.2; pin testids
  - trade-memory-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - recent-entries
  - weekly-review
  - mistake-frequency
  - markdown-export
  - interpretation-panel
  - watchpoints-panel
  - safety-caption

System Ops (/system-ops)
  - system-ops-page
  - judgment-header
  - drivers-panel
  - conflicts-panel
  - system-health
  - migration-status
  - protocol-cards
  - data-source-strip
  - interpretation-panel
  - watchpoints-panel
  - safety-caption
```

testid names use kebab-case and are stable identifiers — do not change
them again after this slice lands.

## Shared UI changes

```text
frontend/src/shared/ui/
  JudgmentHeader.tsx              NEW — replaces the per-feature copies.
                                       Renders eyebrow / title (with
                                       accent span) / summary /
                                       confidence meter.
  SafetyCaption.tsx               NEW — wraps the existing
                                       *-safety-caption captions under
                                       a uniform `data-testid="safety-
                                       caption"`. Per-tab copy comes
                                       from the API payload's
                                       safetyCaption field.
  EvidencePanels.tsx              EXTEND — DriversPanel /
                                           ConflictsPanel /
                                           InterpretationPanel /
                                           WatchpointsPanel now each
                                           emit `data-testid="drivers-
                                           panel"` /
                                           `conflicts-panel` /
                                           `interpretation-panel` /
                                           `watchpoints-panel`. If
                                           multiple instances exist on
                                           one page, the testid lives
                                           on the canonical root one
                                           only — gate other instances
                                           behind a different prop.
```

The three Slice 13.9 feature-specific JudgmentHeader components
(`NewsJudgmentHeader`, `EventExposureJudgment`, `ProcessJudgmentHeader`)
must be refactored to thin wrappers around the shared `<JudgmentHeader>`
or be deleted in favour of direct shared usage. Either way the visual
result must stay consistent with the existing screenshots in
`prototypes/ui/enhanced_dashboard_mockup/v4_2/screenshots/`.

## API + fixture additions

For the 7 tabs that lack the v4.2 fields, extend their API response
schema (Pydantic camelCase) with:

```text
- judgment: { eyebrow, title, accent, summary, confidence }
- drivers: list[{ score, title, note }]
- conflicts: list[{ title, note }]
- watchpoints: list[{ title, note }]
- interpretation: { verdict, whyItMatters, whatRemainsUncertain }
- safetyCaption: str
```

Mirror the fixture additions in `api/fixtures/<tab>.py` AND
`frontend/src/mocks/fixtures/<tab>.fixture.ts` so React Query can fall
back to deterministic content when the FastAPI container is offline.

Tabs already carrying these fields (news / event-radar / trade-memory)
keep their existing schemas — only the testid contract changes there.

## Structural test rewrite

Rewrite `frontend/e2e/visual/all-tabs.visual.spec.ts` so each route
test reads from a table:

```ts
const ROUTES = [
  {
    label: "control-room",
    path: "/",
    eyebrow: "GLOBAL OPERATING VERDICT",
    safetyCategory: "Global operating posture",
    requiredTestIds: [
      "control-room-grid",
      "judgment-header",
      "drivers-panel",
      "conflicts-panel",
      "operating-state-hero",
      "portfolio-market-tape",
      "guard-stack",
      "catalyst-watch-summary",
      "watchlist-card",
      "interpretation-panel",
      "watchpoints-panel",
      "safety-caption",
    ],
    screenshotName: "control-room.png",
  },
  // … 9 more entries
];
```

Per-route assertions (structural, untagged so they run on
`npm run test:e2e`):

```text
- os-tray + ticker-strip visible.
- Every entry in requiredTestIds has at least one visible element.
- The judgment-header element contains the eyebrow text exactly.
- The safety-caption element contains the safetyCategory substring.
- FORBIDDEN_EXECUTION_LABELS do not appear in the body.
- "sell-the-news" descriptive idiom NOT flagged.
```

`@visual` half stays the same shape (mask clock + ticker-strip,
maxDiffPixelRatio=0.03) and is what `npm run test:visual` runs once
baselines are committed.

## Required tests

```text
frontend/e2e/visual/all-tabs.visual.spec.ts     (rewritten — strict)
frontend/e2e/judgment-header.spec.ts            (NEW — confidence
                                                 meter rendering /
                                                 accent rendering /
                                                 shared JudgmentHeader
                                                 fallback behaviour)

tests/test_api_control_room.py        — add judgment / drivers / conflicts /
                                        watchpoints / safetyCaption
                                        contract assertions.
tests/test_api_market_kernel.py       — same.
tests/test_api_analysis_workspace.py  — same.
tests/test_api_symbol_lab.py          — same.
tests/test_api_risk_firewall.py       — same.
tests/test_api_mission_control.py     — same.
tests/test_api_system_ops.py          — same.
tests/test_api_news_intelligence.py   — only the safety caption /
                                        testid contract assertions
                                        need pinning (judgment block
                                        already present).
tests/test_api_event_radar.py         — same as news.
tests/test_api_trade_memory.py        — same as news.
```

Existing tests for the 13.7 / 13.8 routes that currently assert on the
v4.1-era schema fields must be updated, not removed.

## Verification commands

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q
python3 -m ruff check finskillos api tests

cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e            # structural — must pass before screenshots
npm run test:visual:update  # once UI is stable, regenerate baselines
                            # inside docker e2e profile only
npm run test:visual         # parity gate after baselines are committed
```

Docker:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:e2e
docker compose --profile e2e run --rm e2e npm run test:visual:update  # bootstrap PNGs
git add frontend/e2e/visual/*-snapshots/*.png
docker compose --profile e2e run --rm e2e npm run test:visual         # parity gate
```

## Completion placeholder

```text
Status: PARTIAL_AS_V4_2_CONTRACT_IMPLEMENTED_DOCKER_STRUCTURAL_PASS (2026-05-23)

Tabs upgraded to v4.2 hierarchy:
- Control Room
- Market Kernel
- Analysis Workspace
- Symbol Lab
- Risk Firewall
- Mission Control
- System Ops
- News / Catalyst / Trade Memory testid + shared header contract aligned

Shared components added/refactored:
- frontend/src/shared/ui/JudgmentHeader.tsx
- frontend/src/shared/ui/SafetyCaption.tsx
- EvidencePanels default canonical testids
- NewsJudgmentHeader / EventExposureJudgment / ProcessJudgmentHeader now wrap shared JudgmentHeader

API schema fields added:
- Shared common JudgmentHeader / EvidenceDriver / EvidenceConflict /
  EvidenceWatchpoint / IntegratedInterpretation
- v4.2 fields added to 13.6 / 13.7 / 13.8 response schemas

Fixture additions:
- api/fixtures/_v42.py helper
- Matching backend + frontend fixture blocks for all 7 previously missing tabs

Structural test rewrites:
- frontend/e2e/visual/all-tabs.visual.spec.ts rewritten to assert per-route
  required testids, judgment eyebrow, safety caption category, and forbidden
  execution labels

Screenshot baselines committed:
- Not yet. Requires Docker e2e visual-update flow after frontend verification.

Tests added:
- frontend/e2e/judgment-header.spec.ts
- tests/test_api_v42_contract.py

Notes:
- System Ops now includes explicit System Health and Migration Status panels.
- Missing Data panel now renders a stable empty state so the testid contract
  is always visible.

Verification:
- python3 -m compileall app.py finskillos api scripts -> PASS
- python3 -m pytest tests -q -> PASS
- python3 -m ruff check finskillos api tests -> PASS
- docker compose -f docker-compose.yml --profile e2e build e2e -> PASS
- docker compose -f docker-compose.yml build api web -> PASS
- docker compose -f docker-compose.yml --profile e2e run --rm e2e \
  npx playwright test e2e/risk-mission-ops.spec.ts \
  e2e/visual/all-tabs.visual.spec.ts \
  --grep "risk-firewall|mission-control|system-ops|Risk Firewall|Mission Control|System Ops" \
  --grep-invert @visual -> PASS (8 passed)

Known issues:
- Local host npm/node is intentionally not the verification path in this WSL
  shell. Use Docker e2e images.
- Full all-tabs `npm run test:e2e` still needs a complete Docker pass.
- Screenshot baselines still need `npm run test:visual:update` inside Docker
  e2e before the visual parity gate can pass.
```

## Stop condition

Stop after 13.11. Do not start 14_Deployment unless the user
explicitly asks. The 14 slice body is still placeholder.
