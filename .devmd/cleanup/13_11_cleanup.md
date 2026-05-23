# 13.11 Cleanup — Finalize v4.2 UI Completion Gate Before Deployment

## Purpose

Slice 13.11 moved the React app much closer to the intended v4.2 Evidence-to-Judgment UI, but it is still **not complete enough to hand off to deployment**.

Current status:

```text
13.11 React UI Completion Audit + v4.2 Parity Polish: PARTIAL PASS
```

This cleanup must close the remaining blockers:

```text
1. Catalyst Watch likely fails the all-tabs structural test because `date-status-badges` is missing.
2. Manual Article over-cap POST test conflicts with Pydantic validation and may return 422 instead of structured 200 / REJECTED.
3. Required 13.9 backend API tests are missing or incomplete.
4. Full Docker structural e2e has not been run across all tabs.
5. Screenshot baselines are still not committed.
6. 13.11 completion note still says PARTIAL.
```

The goal is to turn 13.11 from:

```text
PARTIAL_AS_V4_2_CONTRACT_IMPLEMENTED_DOCKER_STRUCTURAL_PASS
```

into:

```text
DONE_AS_V4_2_UI_COMPLETION_PARITY_GATE_V0
```

Do **not** start deployment work in this cleanup.

---

## Read First

Read these files in order:

```text
.devmd/13_9_React_News_Events_TradeMemory.md
.devmd/13_10_React_Prototype_Parity_Visual_QA.md
.devmd/13_11_UI_Completeness_Parity.md

api/main.py
api/schemas/news_intelligence.py
api/routes/news_intelligence.py
api/routes/event_radar.py
api/routes/trade_memory.py
api/schemas/common.py
api/fixtures/event_radar.py
api/fixtures/trade_memory.py
api/fixtures/news_intelligence.py

frontend/e2e/visual/all-tabs.visual.spec.ts
frontend/e2e/news-events-memory.spec.ts
frontend/e2e/judgment-header.spec.ts
frontend/e2e/visual/README.md
frontend/src/features/events/components/EventRiskTable.tsx
frontend/src/features/events/components/EventStatusBadge.tsx
frontend/src/shared/ui/JudgmentHeader.tsx
frontend/src/shared/ui/SafetyCaption.tsx
frontend/src/shared/ui/EvidencePanels.tsx
frontend/package.json
frontend/package-lock.json
docker-compose.yml
frontend/Dockerfile.e2e
```

---

## Cleanup Scope

Allowed:

```text
- Fix missing / mismatched testids required by 13.11 all-tabs structural test.
- Fix ManualArticleInput summary-length validation so route-level REJECTED response is returned.
- Add missing backend API tests for 13.9 endpoints.
- Run full Docker structural e2e, not a grep-limited subset.
- Generate and commit all-tabs visual baseline PNGs from Docker e2e only.
- Update frontend / API metadata to 13.11 if still stale.
- Update .devmd/13_11 completion note from PARTIAL to DONE only after tests and baselines are complete.
```

Not allowed:

```text
- Start .devmd/14_Deployment_Operations.md.
- Add brokerage / execution / order endpoints.
- Add live external news / market data providers.
- Remove Streamlit debug/admin UI.
- Redesign the product again.
- Weaken no-execution / interpretation-first safety wording.
```

---

# Required Tasks

## 1. Add missing `date-status-badges` testid

The 13.11 all-tabs structural spec requires Catalyst Watch to expose:

```text
date-status-badges
```

Current likely issue:

```text
EventRiskTable renders EventStatusBadge, but no element exposes data-testid="date-status-badges".
```

Update one of these files:

```text
frontend/src/features/events/components/EventRiskTable.tsx
frontend/src/features/events/components/EventStatusBadge.tsx
```

Recommended minimal fix in `EventRiskTable.tsx`:

```tsx
<td data-testid="date-status-badges">
  <EventStatusBadge status={event.dateStatus} toneMap={toneMap} />
</td>
```

Multiple elements with the same testid are acceptable because the structural test uses `.first()`.

Acceptance:

```text
- /catalyst-watch exposes at least one visible data-testid="date-status-badges".
- Existing event status badge styling remains unchanged.
- Event risk score wording remains preparation / exposure only.
```

---

## 2. Fix manual article over-cap response contract

Current likely issue:

```text
ManualArticleInput.summary has max_length=MAX_SUMMARY_CHARS.
```

Because of this, POSTing a 700-character summary may return FastAPI/Pydantic `422` before the route handler can return the intended structured response:

```json
{
  "status": "REJECTED",
  "detail": "summary_too_long"
}
```

Update:

```text
api/schemas/news_intelligence.py
```

Change request model only:

```python
class ManualArticleInput(CamelModel):
    ...
    summary: str = Field(..., min_length=1)
```

Do **not** remove max length from response article summaries:

```python
class NewsArticleVM(CamelModel):
    summary: str = Field(..., max_length=MAX_SUMMARY_CHARS)
```

Keep the route-level check in:

```text
api/routes/news_intelligence.py
```

so this path returns:

```text
200 OK
status = REJECTED
detail = summary_too_long
```

Acceptance:

```text
- POST /api/news-intelligence/manual-article with summary length > 500 returns 200.
- Response status is REJECTED.
- Response detail is summary_too_long.
- Response does not expose a raw FastAPI validation payload for this case.
- Short valid summaries still pass the schema.
```

---

## 3. Add missing backend API tests for 13.9 endpoints

The 13.9 devmd required these files, but they were not present during review:

```text
tests/test_api_news_intelligence.py
tests/test_api_event_radar.py
tests/test_api_trade_memory.py
```

Create them.

### `tests/test_api_news_intelligence.py`

Required tests:

```python
def test_news_intelligence_snapshot_exposes_v42_contract() -> None:
    client = TestClient(create_app())
    body = client.get("/api/news-intelligence").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["impactMap"]
    assert body["manualEntryRules"]["maxSummaryChars"] == 500
    assert "Descriptive narrative view only" in body["safetyCaption"]
```

```python
def test_manual_article_rejects_over_cap_summary_with_structured_response() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "Probe",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "x" * 700,
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "summary_too_long"
```

```python
def test_manual_article_rejects_forbidden_wording() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/news-intelligence/manual-article",
        json={
            "title": "지금 사라",
            "source": "Probe",
            "url": "https://example.com/probe",
            "publishedAt": "2026-05-20T12:00:00+00:00",
            "summary": "Short descriptive summary only.",
            "affectedTickers": [],
            "theme": None,
            "eventKey": None,
            "sentiment": "UNKNOWN",
            "riskLevel": "UNKNOWN",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert "forbidden_wording" in body["detail"]
```

### `tests/test_api_event_radar.py`

Required tests:

```python
def test_event_radar_snapshot_exposes_v42_contract() -> None:
    client = TestClient(create_app())
    body = client.get("/api/event-radar").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["dateStatusBadgeTone"]
    assert "preparation / exposure score" in body["safetyCaption"]
    assert "price direction prediction" in body["safetyCaption"]
```

```python
def test_manual_event_rejects_confirmed_manual_seed() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/event-radar/manual-event",
        json={
            "title": "Should be rejected",
            "eventType": "EARNINGS",
            "dateStatus": "CONFIRMED",
            "startDate": "2026-06-01",
            "endDate": None,
            "source": "manual_seed",
            "sourceUrl": None,
            "description": None,
            "importanceScore": "1.0",
            "ticker": None,
            "sector": None,
            "theme": None,
            "eventKey": None,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
    assert body["detail"] == "confirmed_requires_external_source"
```

```python
def test_seed_sample_events_returns_structured_json() -> None:
    client = TestClient(create_app())
    response = client.post("/api/event-radar/seed-sample-events")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"OK", "NOOP", "ERROR"}
    assert "message" in body
    assert "detail" in body
```

### `tests/test_api_trade_memory.py`

Required tests:

```python
def test_trade_memory_snapshot_exposes_v42_contract() -> None:
    client = TestClient(create_app())
    body = client.get("/api/trade-memory").json()

    assert body["judgment"]
    assert body["drivers"]
    assert body["conflicts"]
    assert body["weeklyReview"]["markdown"]
    assert body["mistakeFrequency"]
    assert "Reflection / process review" in body["safetyCaption"]
```

```python
def test_trade_memory_weekly_review_endpoint_returns_markdown() -> None:
    client = TestClient(create_app())
    body = client.get("/api/trade-memory/weekly-review").json()
    assert body["markdown"]
    assert body["tradeCount"] >= 0
```

```python
def test_trade_entry_rejects_forbidden_wording() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/trade-memory/entries",
        json={
            "tradeDate": "2026-05-19",
            "ticker": "TSLA",
            "side": "LONG",
            "notes": "지금 사라",
            "mistakeTags": [],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REJECTED"
```

Acceptance:

```text
- New backend tests pass.
- Tests verify structure and safety seams, not just route existence.
```

---

## 4. Update stale metadata if needed

Check:

```text
frontend/package.json
frontend/package-lock.json
api/main.py
```

If still stale, update:

```json
{
  "version": "0.13.11",
  "description": "FinSkillOS v4.2 React Evidence-to-Judgment cockpit through Slice 13.11."
}
```

Update lockfile root package metadata:

```bash
cd frontend
npm install --package-lock-only
```

Update FastAPI app version/description if stale:

```python
version="0.13.11"
```

Description should mention:

```text
v4.2 React Evidence-to-Judgment cockpit
```

Acceptance:

```text
- package.json and package-lock root version match.
- api/main.py version reflects 13.11.
- Description does not still say v4.1 or through Slice 13.8 / 13.9.
```

---

## 5. Run full Docker structural e2e, not a grep-limited subset

Current 13.11 completion note only records a grep-limited pass:

```text
risk-firewall|mission-control|system-ops
```

That is not enough.

Run:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:e2e
```

This must include:

```text
frontend/e2e/visual/all-tabs.visual.spec.ts structural block
frontend/e2e/news-events-memory.spec.ts
frontend/e2e/market-analysis-symbol.spec.ts
frontend/e2e/risk-mission-ops.spec.ts
frontend/e2e/judgment-header.spec.ts
frontend/e2e/navigation.spec.ts
frontend/e2e/theme.spec.ts
frontend/e2e/responsive.spec.ts
```

If `npm run test:e2e` does not include all structural specs, adjust Playwright config or package scripts so structural e2e is complete while still excluding `@visual` screenshot tests.

Acceptance:

```text
- Full Docker structural e2e passes without grep narrowing.
- all-tabs structural contract passes for all 10 routes.
- No required testid is missing.
- No forbidden execution caption appears.
```

---

## 6. Ensure visual baseline update writes PNGs to the host repo

Important: If the e2e container is image-only and has no bind mount for `frontend/e2e`, running `test:visual:update` inside the container may generate PNGs inside the disposable container and lose them on `--rm`.

Before generating baselines, inspect:

```text
docker-compose.yml
```

The e2e service must persist snapshots back to the repository. One acceptable pattern:

```yaml
e2e:
  volumes:
    - ./frontend/e2e:/work/frontend/e2e
    - ./frontend/playwright-report:/work/frontend/playwright-report
    - ./frontend/test-results:/work/frontend/test-results
```

If the current e2e service does not bind-mount the e2e directory, add the mount or use another explicit copy-out workflow.

Then run:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual:update
```

Verify files exist on host:

```bash
find frontend/e2e/visual -path '*all-tabs.visual.spec.ts-snapshots*' -name '*.png' -print
```

Expected route baseline PNGs:

```text
control-room.png
market-kernel.png
analysis-workspace.png
symbol-lab.png
risk-firewall.png
mission-control.png
news-intelligence.png
catalyst-watch.png
trade-memory.png
system-ops.png
```

Then commit them:

```bash
git add frontend/e2e/visual/*-snapshots/*.png
```

Acceptance:

```text
- all-tabs visual snapshot PNGs exist in the working tree.
- PNGs are generated from Docker e2e, not local WSL host.
- `npm run test:visual` can compare against committed baselines.
```

---

## 7. Run visual parity gate after baselines are committed

After baseline PNGs are generated and present on the host:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual
```

Acceptance:

```text
- `npm run test:visual` passes inside Docker e2e.
- No route fails due to missing baseline.
- Any visual diff above threshold is investigated instead of blindly accepted.
```

---

## 8. Update `.devmd/13_11_UI_Completeness_Parity.md` completion state

Only after all previous tasks pass, update:

```text
.devmd/13_11_UI_Completeness_Parity.md
```

Replace the current PARTIAL completion state with:

```text
Status: DONE_AS_V4_2_UI_COMPLETION_PARITY_GATE_V0 (YYYY-MM-DD)

Cleanup completed:
- Added missing Catalyst Watch date-status-badges testid.
- Fixed ManualArticleInput summary validation so over-cap input returns structured REJECTED response instead of 422.
- Added backend API tests:
  - tests/test_api_news_intelligence.py
  - tests/test_api_event_radar.py
  - tests/test_api_trade_memory.py
- Updated stale frontend/API metadata to 0.13.11 if needed.
- Full Docker structural e2e passed with no grep narrowing.
- Generated all-tabs visual baselines from Docker e2e.
- Committed all-tabs snapshot PNGs.
- Docker visual parity gate passed.

Verification:
- python3 -m compileall app.py finskillos api scripts
- python3 -m pytest tests -q
- python3 -m ruff check finskillos api tests
- docker compose up -d postgres api web
- docker compose --profile e2e run --rm e2e npm run test:e2e
- docker compose --profile e2e run --rm e2e npm run test:visual:update
- docker compose --profile e2e run --rm e2e npm run test:visual

Remaining:
- Pixel-perfect parity is still not required; the accepted gate is structural v4.2 hierarchy + screenshot regression baseline.
- Deployment hardening remains deferred to `.devmd/14_Deployment_Operations.md`.
```

Do not mark 13.11 as DONE until:

```text
full structural e2e passes
visual snapshots are committed
visual parity test passes
```

---

# Verification Commands

Run from repository root:

```bash
python3 -m compileall app.py finskillos api scripts
python3 -m pytest tests -q
python3 -m ruff check finskillos api tests
```

Run Docker structural e2e:

```bash
docker compose up -d postgres api web
docker compose --profile e2e run --rm e2e npm run test:e2e
```

Generate and commit baselines:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual:update
find frontend/e2e/visual -path '*all-tabs.visual.spec.ts-snapshots*' -name '*.png' -print
git add frontend/e2e/visual/*-snapshots/*.png
```

Run visual gate:

```bash
docker compose --profile e2e run --rm e2e npm run test:visual
```

Manual smoke:

```text
- Open web app.
- Visit all 10 routes.
- Every tab shows Judgment Header, Primary Drivers, Conflicts, Evidence, Integrated Interpretation, Watchpoints, Safety Caption.
- Catalyst Watch shows date status badges.
- News manual article form says short summaries only and has no full-body field.
- Trade Memory side selector exposes LONG / SHORT / WATCH / EXIT_REVIEW / OTHER only.
- No buy/sell/order/execution controls appear.
```

---

# Stop Condition

Stop after 13.11 cleanup.

Do **not** begin:

```text
.devmd/14_Deployment_Operations.md
```

until the user explicitly asks.
