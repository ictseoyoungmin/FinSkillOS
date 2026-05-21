# 13.8 Cleanup — React Risk/Mission/Ops Hardening + v4.2 Handoff for 13.9

## Purpose

Slice 13.7 and 13.8 are structurally complete enough to proceed, but a small cleanup should be done before starting Slice 13.9.

Current status:

```text
13.7 React Market / Analysis / Symbol: PASS
13.8 React Risk / Mission / System Ops: PASS with minor cleanup
```

This cleanup should harden the current implementation and prepare Slice 13.9 to use the newer Evidence-to-Judgment UX baseline.

The important new prototype path is:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

Slice 13.9 should read that file and use it as the UX direction for:

```text
News Intelligence
Catalyst Watch
Trade Memory
```

Do not implement 13.9 in this cleanup. Only update the repository so the next slice can start cleanly.

---

## Read First

Read these files in order:

```text
.devmd/13_6_Frontend_Migration_Shell.md
.devmd/13_7_React_Market_Analysis_Symbol.md
.devmd/13_8_React_Risk_Mission_Ops.md
.devmd/13_9_React_News_Events_TradeMemory.md
.devmd/13_10_React_Prototype_Parity_Visual_QA.md

prototypes/ui/enhanced_dashboard_mockup/index.html
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html

frontend/package.json
frontend/package-lock.json
frontend/Dockerfile.e2e
docker-compose.yml

api/fixtures/risk_firewall.py
api/routes/system_ops.py
api/schemas/system_ops.py

frontend/e2e/_helpers.ts
frontend/e2e/risk-mission-ops.spec.ts
frontend/e2e/market-analysis-symbol.spec.ts
frontend/e2e/navigation.spec.ts
```

If the v4.2 prototype file is missing locally, stop and report that it must be copied into:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

before starting Slice 13.9.

---

## Cleanup Scope

Allowed:

```text
- Fix Playwright Docker image version mismatch.
- Clean up slightly advisory Risk Firewall wording.
- Normalize prototype path references across devmd docs.
- Bump frontend metadata from Slice 13.6 to current Slice 13.8 status.
- Update 13.9 devmd to explicitly use the v4.2 Evidence-to-Judgment prototype.
- Add or adjust tests for wording safety if needed.
- Update 13.8 completion note with cleanup status.
```

Not allowed:

```text
- Implement News Intelligence / Catalyst Watch / Trade Memory.
- Add new external news APIs.
- Add brokerage, execution, order, buy, or sell features.
- Remove Streamlit debug/admin UI.
- Rewrite all existing 13.7/13.8 pages to v4.2.
- Start 13.10 visual parity.
```

---

# Required Cleanup Tasks

## 1. Align Playwright Docker image with package version

Current issue:

```text
frontend/package.json / package-lock.json use @playwright/test ^1.60.0
frontend/Dockerfile.e2e uses mcr.microsoft.com/playwright:v1.49.1-noble
```

This can cause browser revision mismatch inside the e2e Docker container.

Update:

```dockerfile
FROM mcr.microsoft.com/playwright:v1.49.1-noble
```

to:

```dockerfile
FROM mcr.microsoft.com/playwright:v1.60.0-noble
```

in:

```text
frontend/Dockerfile.e2e
```

Do not downgrade `@playwright/test` unless `v1.60.0-noble` is unavailable in the environment.

After the change, confirm that this command remains the intended workflow:

```bash
docker compose --profile e2e run --rm e2e
```

---

## 2. Soften advisory wording in Risk Firewall fixture

Current Risk Firewall protocol wording is slightly action-advisory:

```text
Consider reducing exposure size.
```

This is not a direct buy/sell directive, but FinSkillOS should remain an interpretation and constraint system.

Update in:

```text
api/fixtures/risk_firewall.py
```

Replace the limited protocol description with state/constraint wording.

Preferred:

```text
Exposure-size review remains required while concentration or overheat flags remain active.
```

or:

```text
Exposure-size constraint remains active while concentration or overheat flags remain active.
```

Avoid:

```text
Consider reducing exposure size.
Reduce position.
Trim exposure.
Buy.
Sell.
Execute.
Order.
```

Also update the matching frontend fixture if a copied description exists:

```text
frontend/src/mocks/fixtures/riskFirewall.fixture.ts
```

Run the existing forbidden wording tests after this change.

---

## 3. Normalize prototype path references

Earlier docs still reference:

```text
prototypes/ui/enhanced_dashboard_mockup/finskillos_v4_1_product_cockpit_index.html
```

The repository convention should now be:

```text
prototypes/ui/enhanced_dashboard_mockup/index.html
```

for v4.1 baseline, and:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

for the new Evidence-to-Judgment baseline.

Update prototype path references in:

```text
.devmd/13_7_React_Market_Analysis_Symbol.md
.devmd/13_8_React_Risk_Mission_Ops.md
.devmd/13_9_React_News_Events_TradeMemory.md
.devmd/13_10_React_Prototype_Parity_Visual_QA.md
```

Recommended wording:

```text
v4.1 visual shell baseline:
prototypes/ui/enhanced_dashboard_mockup/index.html

v4.2 Evidence-to-Judgment UX baseline:
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

Do not leave the old long v4.1 filename in any devmd read-first section unless the file actually exists and is intentionally used.

---

## 4. Update frontend package metadata

`frontend/package.json` still describes the app as Slice 13.6.

Update:

```json
{
  "version": "0.13.8",
  "description": "FinSkillOS v4 React cockpit — Vite + React shell through Slice 13.8."
}
```

Also regenerate or update `frontend/package-lock.json` so the root package version matches.

Command:

```bash
cd frontend
npm install --package-lock-only
```

or simply:

```bash
npm install
```

Do not change dependency versions unless npm forces a lockfile-only metadata update.

---

## 5. Update 13.9 devmd to use v4.2 Evidence-to-Judgment UX

This is the most important handoff.

Update:

```text
.devmd/13_9_React_News_Events_TradeMemory.md
```

so that Slice 13.9 reads and follows:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

Add the following section near the top.

```md
## UX Direction — v4.2 Evidence-to-Judgment

Slice 13.9 must use the v4.2 Evidence-to-Judgment prototype as the primary UX direction:

```text
prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
```

For each tab, avoid a simple table/card dump. The page should read as:

```text
Judgment Header
→ Primary Drivers
→ Conflicts / Uncertainty
→ Evidence Details
→ Integrated Interpretation
→ Watchpoints / Review Conditions
```

This does not mean implementing pixel-perfect v4.2 styling in this slice. It means the information hierarchy must let the user understand how raw news/events/journal data combines into a judgment-support view.

Allowed judgment types:
- narrative state
- event exposure state
- process/reflection state
- data freshness state
- portfolio relevance state

Forbidden:
- direct buy/sell recommendation
- order/execution controls
- guaranteed return language
```

Then make the 13.9 tab requirements more explicit as below.

---

# Required 13.9 UX Details to Add to `.devmd/13_9_React_News_Events_TradeMemory.md`

## News Intelligence — v4.2 target

News Intelligence should answer:

```text
What narrative is affecting my portfolio, and what evidence supports that interpretation?
```

Required structure:

```text
Judgment Header:
- Narrative Judgment
- confidence
- dominant theme
- portfolio relevance
- event linkage
- sentiment / risk tone

Primary Drivers:
- affected holdings
- theme exposure
- linked event count
- source quality / freshness

Conflicts / Uncertainty:
- positive narrative vs event volatility
- article count vs source/date confidence
- broad market news vs holding-specific relevance

Evidence Details:
- holdings-relevant news
- impact map
- event-linked news
- manual article entry

Integrated Interpretation:
- what today’s news means for portfolio context
- why it matters
- what remains uncertain

Watchpoints:
- source confirmation
- change in linked event status
- sudden cluster in same theme/ticker
```

Required components:

```text
features/news/components/NewsJudgmentHeader.tsx
features/news/components/HoldingsRelevantNews.tsx
features/news/components/NewsImpactMap.tsx
features/news/components/EventLinkedNewsPanel.tsx
features/news/components/ManualArticleEntry.tsx
features/news/components/NewsWatchpointsPanel.tsx
```

API targets remain:

```text
GET /api/news-intelligence
POST /api/news-intelligence/manual-article
```

Manual article entry must avoid storing full copyrighted article bodies. Store only:

```text
title
source
url
published_at
short_summary
affected_tickers
theme
event_key
sentiment/risk tags
```

---

## Catalyst Watch / Event Radar — v4.2 target

Catalyst Watch should answer:

```text
Which upcoming events create exposure, and why is the event risk score high or low?
```

Required structure:

```text
Judgment Header:
- Event Exposure Judgment
- confidence
- highest-risk event
- cluster status
- portfolio-linked exposure
- date-confidence mix

Primary Drivers:
- portfolio exposure
- days to event
- date status
- regime multiplier
- linked news count

Conflicts / Uncertainty:
- confirmed event vs speculative event
- high news attention vs low date confidence
- event risk score is not price prediction

Evidence Details:
- upcoming event table
- date status badges
- high-risk events
- holdings-linked events
- linked news
- manual event entry
- sample event seed action

Integrated Interpretation:
- why the event deserves attention
- how it relates to portfolio exposure
- what makes the score uncertain

Watchpoints:
- speculative → reported/confirmed date status transition
- linked news count increase
- regime shift increasing/decreasing event multiplier
```

Required event status badges:

```text
CONFIRMED
WINDOW
TENTATIVE
REPORTED
SPECULATIVE
```

Required components:

```text
features/events/components/EventExposureJudgment.tsx
features/events/components/EventRiskTable.tsx
features/events/components/EventStatusBadge.tsx
features/events/components/HighRiskEventsPanel.tsx
features/events/components/HoldingsLinkedEventsPanel.tsx
features/events/components/EventScoreDrivers.tsx
features/events/components/ManualEventEntry.tsx
features/events/components/EventLinkedNewsPanel.tsx
```

API targets remain:

```text
GET /api/event-radar
POST /api/event-radar/manual-event
POST /api/event-radar/seed-sample-events
```

Important wording rule:

```text
Event risk score = preparation / exposure score only.
It must never be described as price direction prediction.
```

---

## Trade Memory — v4.2 target

Trade Memory should answer:

```text
What repeated behavior pattern is visible, and what should I review before the next week?
```

Required structure:

```text
Judgment Header:
- Process Judgment
- confidence
- best condition
- weakest condition
- repeated mistake
- review priority

Primary Drivers:
- recent entries
- PnL by regime
- PnL by sector/theme
- PnL by strategy
- mistake frequency
- emotion tags before losses

Conflicts / Uncertainty:
- good market regime vs poor process behavior
- high win rate vs clustered mistakes
- short sample size limitations

Evidence Details:
- recent entries table
- add journal entry form
- weekly review panel
- performance by regime
- performance by sector/theme
- performance by strategy
- mistake frequency
- copyable weekly review markdown

Integrated Interpretation:
- what pattern appeared this week
- what condition helped
- what condition harmed
- what review condition matters next

Watchpoints:
- chasing before event windows
- oversizing in overheat regime
- emotion tag clustering before losses
```

Required components:

```text
features/trades/components/ProcessJudgmentHeader.tsx
features/trades/components/RecentEntriesTable.tsx
features/trades/components/TradeEntryForm.tsx
features/trades/components/WeeklyReviewPanel.tsx
features/trades/components/PerformanceByRegime.tsx
features/trades/components/PerformanceBySectorTheme.tsx
features/trades/components/PerformanceByStrategy.tsx
features/trades/components/MistakeFrequencyPanel.tsx
features/trades/components/WeeklyMarkdownExport.tsx
features/trades/components/TradeMemoryWatchpoints.tsx
```

API targets remain:

```text
GET /api/trade-memory
POST /api/trade-memory/entries
GET /api/trade-memory/weekly-review
```

---

## 6. Add a small 13.8 cleanup note to `.devmd/13_8_React_Risk_Mission_Ops.md`

Append:

```text
13.8 Cleanup Status: DONE_AS_REACT_RISK_MISSION_OPS_CLEANUP_V0 (YYYY-MM-DD)

Cleanup implemented:
- Aligned Playwright e2e Docker image with @playwright/test version.
- Softened Risk Firewall limited protocol wording from advisory action to constraint-state wording.
- Normalized prototype path references:
  - v4.1 shell baseline: prototypes/ui/enhanced_dashboard_mockup/index.html
  - v4.2 Evidence-to-Judgment baseline: prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
- Updated frontend package metadata to 0.13.8.
- Updated 13.9 instructions to use the v4.2 Evidence-to-Judgment UX direction.

Remaining:
- 13.9 still not implemented.
- 13.7/13.8 pages are functionally complete but not fully refactored into v4.2 Judgment Header structure.
- Full screenshot parity remains deferred to 13.10.
```

---

# Tests / Verification

Run from repository root:

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m ruff check finskillos api tests
python3 -m pytest tests -q
```

Run from frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run test:e2e
```

Docker e2e smoke:

```bash
docker compose up -d postgres api web
docker compose --profile e2e build e2e
docker compose --profile e2e run --rm e2e
```

Optional visual baseline is still separate:

```bash
cd frontend
npm run test:visual
```

---

# Acceptance Criteria

13.8 cleanup is complete when:

```text
- frontend/Dockerfile.e2e uses a Playwright image matching @playwright/test.
- frontend/package.json version/description reflects Slice 13.8.
- package-lock root package version matches package.json.
- Risk Firewall limited protocol wording is constraint-state wording, not advisory action wording.
- devmd prototype paths are normalized.
- .devmd/13_9_React_News_Events_TradeMemory.md explicitly references:
  prototypes/ui/enhanced_dashboard_mockup/v4_2/finskillos_v4_2_evidence_judgment_mockup.html
- 13.9 instructions clearly require Evidence-to-Judgment information hierarchy.
- Existing API and frontend tests pass.
- No direct execution / buy / sell / order wording is introduced.
```

Stop after 13.8 cleanup.

Do not begin 13.9 implementation until the user explicitly asks.
