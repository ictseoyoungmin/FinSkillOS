# Project Diagnostics

Updated: 2026-06-02

This file records cross-tab implementation and visual diagnostics for the current
FinSkillOS cockpit. It is intentionally separate from executable slice files:
future diagnostics can update this document without implying that a new slice
has started.

## Scope

- Inspect functional wiring between frontend, API routes, and shared shell state.
- Inspect visual continuity from each tab's top through lower content.
- Preserve FinSkillOS descriptive-only safety language; no execution or order
  recommendation language should be introduced by diagnostic notes.
- Use Docker-based validation only when executing the app, tests, or builds.

## 2026-06-02 Initial Static Findings

### D-001 CORS methods do not match exposed mutation routes

Severity: P1 functional wiring

Status: fixed 2026-06-02

`api/main.py` allows only `GET`, `POST`, and `OPTIONS` for CORS, but the API and
frontend now expose `PUT` and `DELETE` paths:

- Trade Memory update/delete:
  - `frontend/src/features/trades/api.ts`
  - `api/routes/trade_memory.py`
- Symbol subscription folder member removal:
  - `frontend/src/features/symbol/api.ts`
  - `api/routes/symbol_lab.py`

Impact: cross-origin frontend/API deployments can fail browser preflight for
edit/delete flows even though the FastAPI routes exist.

Fix:

- `api/main.py` now allows `GET`, `POST`, `PUT`, `DELETE`, and `OPTIONS`.
- The FastAPI app description now reflects the current safe mutation boundary:
  System Ops protocols, watchlist organization, and Trade Memory journal records.
- `tests/test_api_health.py` covers CORS preflight for existing mutation methods.

Verification:

```bash
docker compose -f docker-compose.yml build api
docker compose -f docker-compose.yml run --rm api python -m ruff check api/main.py tests/test_api_health.py
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_api_health.py -q
```

Result: ruff passed; focused pytest passed.

### D-002 Top tray DB pill is hard-coded to live

Severity: P1 visual/operational state coherence

Status: fixed 2026-06-02

`OsShell` reads `/api/system-status` and passes DB state to the unavailable
banner and footer status bar, but `OsTopTray` renders `DB · Live` unconditionally.

Impact: the shell can show a DB unavailable banner/footer while the top tray
still says `DB · Live`, creating contradictory operational evidence.

Fix:

- `OsShell` now passes `systemStatus.dbStatus` into `OsTopTray`.
- `OsTopTray` renders `DB · LIVE` with success tone or `DB · MISSING` with
  danger tone from the same `/api/system-status` contract used by the banner and
  footer.
- `frontend/e2e/db-unavailable.spec.ts` covers both states.

Verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/db-unavailable.spec.ts --project=chromium --workers=1
```

Result: web build passed; focused Playwright passed (2 tests).

### D-003 API failure handling is inconsistent across tabs

Severity: P1 data-state honesty

Status: fixed 2026-06-02

Market Kernel and Analysis Workspace surface API errors to React Query so the
page can render an explicit live-unavailable state. Several other tabs still
catch network/4xx errors and return deterministic fixtures directly from the
frontend API wrapper.

Impact: some tabs visibly distinguish failed live reads, while others can show a
fixture payload without a local page-level failure signal.

Fix:

- Control Room, Risk Firewall, Mission Control, News Intelligence, Catalyst
  Watch, Trade Memory, and the System Ops catalogue now surface snapshot read
  failures to React Query instead of returning fixtures inside the API wrapper.
- Each page keeps its deterministic `placeholderData` shape but renders the
  shared `Live data unavailable — showing sample shape, not live data` warning
  pill when the live request fails.
- `SystemStatus` keeps its explicit MISSING fallback because it powers the
  shell-level DB-unavailable contract rather than a product snapshot.
- The existing forced-fixture e2e/visual helper remains intact.

Verification:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
docker compose -f docker-compose.yml up -d web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/live-fetch-pill.spec.ts --project=chromium --workers=1
```

Result: web build passed; focused Playwright live-failure suite passed
(18 passed).

### D-004 Event Risk is live-wired but still named like a placeholder

Severity: P2 terminology / mental model

Status: fixed 2026-06-02

`finskillos/guards/event_risk_guard.py` now consumes Catalyst Watch exposure
summaries, but fixture output still names the row `EVENT_PLACEHOLDER_GUARD` with
the title `Event Placeholder`.

Impact: users can read an implemented live connection as a deferred or fake
feature, especially on Risk Firewall fixture/demo views.

Fix:

- Kept the legacy internal guard id `EVENT_PLACEHOLDER_GUARD` for compatibility.
- Renamed user-visible fixture copy to `Event Exposure` in backend and frontend
  Risk Firewall fixtures.
- Reworded disconnected guard copy away from deferred-slice language and toward
  explicit missing Catalyst Watch evidence.
- Added API/unit regression coverage so the fixture title does not expose
  `Placeholder` while the compatibility id remains stable.

Verification:

```bash
docker compose -f docker-compose.yml build api web
docker compose -f docker-compose.yml run --rm api python -m ruff check finskillos/guards/event_risk_guard.py api/fixtures/risk_firewall.py tests/test_risk_guards.py tests/test_api_risk_firewall.py
docker compose -f docker-compose.yml run --rm api timeout 300 env FINSKILLOS_SKIP_DOTENV=1 python -m pytest tests/test_risk_guards.py tests/test_api_risk_firewall.py -q
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
```

Result: API/web image build passed; ruff passed; focused pytest passed;
frontend production build/type validation passed.

### D-005 Top navigation labels are visually compressed

Severity: P2 visual navigation clarity

The top tray contains 10 module labels in one row and truncates most labels at
1280px. `nav-config.ts` includes module-specific `iconChar`, but `OsTopTray`
renders a generic dot for every module.

Impact: module identity is harder to scan, and the top-level navigation feels
less connected to the command palette's richer module identity.

## 2026-06-02 Full-Scroll Visual Audit

Status: completed.

Method:

- Run the app through Docker.
- Capture every routed tab at desktop size from top to bottom through a
  scroll-container aware Playwright diagnostic.
- Forced product snapshot APIs into fixture mode via `X-FSO-Use-Fixture: 1` so
  content-rich lower panels are deterministic. `/api/system-status` was not
  forced, matching the existing shell query behavior.
- Record page height, viewport count, console/page errors, horizontal overflow,
  and screenshot artifacts.

Artifacts:

- Diagnostic spec: `frontend/e2e/diagnostics/full-scroll-diagnostics.spec.ts`
- Output directory: `frontend/test-results/diagnostics/full-scroll/`
- Per tab outputs: `<tab>.json`, `<tab>-full-page.png`, and
  `<tab>-viewport-<n>.png`.

### Audit Summary

All 10 routed tabs rendered and captured successfully.

| Tab | Workspace height | Scroll stops | Console/page errors | Horizontal overflow |
| --- | ---: | ---: | --- | --- |
| Control Room | 2005 | 4 | none | no |
| Market Kernel | 1613 | 3 | none | no |
| Analysis Workspace | 1756 | 3 | none | no |
| Symbol Lab | 2356 | 4 | none | no |
| Risk Firewall | 1648 | 3 | none | no |
| Mission Control | 1734 | 3 | none | no |
| News Intelligence | 977 | 2 | none | no |
| Catalyst Watch | 1658 | 3 | none | no |
| Trade Memory | 3122 | 6 | none | no |
| System Ops | 1982 | 4 | none | no |

The broad structural result is healthy: there were no browser page errors, no
console errors, and no horizontal overflow at the desktop audit viewport.

### D-006 Shell status contradiction is visible in screenshots

Severity: P1 visual/operational state coherence

Status: fixed 2026-06-02

The full-scroll screenshots confirm D-002 as a visible issue. In fixture-forced
product pages, `/api/system-status` can report missing/partial state in the
footer while the top tray still displays `DB · Live` with success styling.

Observed artifact:

- `frontend/test-results/diagnostics/full-scroll/control-room-viewport-3.png`

Impact: the same viewport can show top-tray DB live while the footer reports
`DB MISSING`. This weakens System Ops / DB-state trust at exactly the place where
the cockpit is supposed to be explicit about sample shape vs live evidence.

Fix: same as D-002. The top tray, banner, and footer now share the system-status
DB state.

### D-007 Sticky ticker strip visually competes with scrolled content

Severity: P2 visual continuity

During internal workspace scrolling, the top tray and ticker strip remain fixed
while the product content scrolls underneath. This is expected from the shell
layout, but in mid/lower screenshots the ticker strip sits directly over the
scrolled content boundary and can make the current content region feel clipped
or partially hidden.

Observed artifacts:

- `frontend/test-results/diagnostics/full-scroll/market-kernel-viewport-2.png`
- `frontend/test-results/diagnostics/full-scroll/symbol-lab-viewport-3.png`
- `frontend/test-results/diagnostics/full-scroll/system-ops-viewport-3.png`

Likely cause:

- `frontend/src/app/layout/os-shell.css` makes `.fso-os-workspace` the scroll
  container inside a `100vh` shell.
- The top tray and ticker strip are outside that scroll container and remain in
  place.

Impact: lower page sections are reachable, but the visual transition from global
market strip to page content reads like an overlay instead of a clear boundary.

### D-008 Lower-page whitespace from uneven fixed column grids

Severity: P2 visual continuity / information density

Several tabs reach their lower content with large empty regions in one column
while the other column continues. This is not a rendering failure, but it makes
the lower page feel visually disconnected.

Observed artifacts:

- `frontend/test-results/diagnostics/full-scroll/control-room-viewport-3.png`
- `frontend/test-results/diagnostics/full-scroll/market-kernel-viewport-2.png`
- `frontend/test-results/diagnostics/full-scroll/catalyst-watch-viewport-2.png`
- `frontend/test-results/diagnostics/full-scroll/trade-memory-viewport-5.png`

Likely causes:

- Control Room uses three explicit columns and per-column flex stacks:
  `frontend/src/pages/control-room/control-room-grid.css`.
- Market Kernel uses a three-column grid:
  `frontend/src/pages/market-kernel/market-kernel.css`.
- Catalyst Watch and Trade Memory use two-column grids:
  `frontend/src/pages/catalyst-watch/catalyst-watch.css`,
  `frontend/src/pages/trade-memory/trade-memory.css`.

Impact: content is present and scrollable, but the lower viewport often contains
one strong information column plus a large dark empty area. This is especially
noticeable in Trade Memory, where the lower form sits on the right while the
left half is mostly empty.

### D-009 Control Room has nested scroll risk

Severity: P2 visual/interaction continuity

Control Room columns have `overflow-y: auto` inside the already scrollable OS
workspace.

Relevant file:

- `frontend/src/pages/control-room/control-room-grid.css`

Impact: at desktop size this did not produce horizontal overflow or page errors,
but it can create a nested-scroll mental model: users may scroll the page while
individual Control Room columns also own independent scroll behavior. This is a
likely source of "I did not see the lower part" confusion in dense dashboards.

### D-010 News Intelligence hides lower secondary evidence behind collapsed state

Severity: P3 default information visibility

News Intelligence lower content is mostly reachable within two scroll stops, but
the `Secondary Evidence` region is collapsed by default behind an `EXPAND`
control.

Observed artifact:

- `frontend/test-results/diagnostics/full-scroll/news-intelligence-viewport-1.png`

Impact: this is not broken, but if the goal is "top-to-bottom review at a
glance," the default screen does not expose holdings/watchpoints/event-linked
details until the user expands the panel.

## Verification

Commands run:

```bash
docker compose -f docker-compose.yml up -d api web
docker compose -f docker-compose.yml --profile e2e run --rm e2e npx playwright test e2e/diagnostics/full-scroll-diagnostics.spec.ts --project=chromium --workers=1
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml run --rm --no-deps web npm run build
```

Results:

- Full-scroll diagnostic Playwright spec: 10 passed.
- Frontend production build/type validation: passed.

Known limits:

- The visual audit forced product snapshot APIs to fixture mode to make all tabs
  content-rich and deterministic. It did not click every expandable drawer or
  mutate data.
- The current diagnostic full-page PNG captures the document viewport, while the
  real scroll occurs inside `main[data-testid="os-workspace"]`. Use the
  `*-viewport-<n>.png` files for true top-to-bottom inspection.
