# 13. State Vocabulary & Data Source Contract

> Current status: v2.1 / v4.2 authoritative state glossary.
> This document pins the terminology used across API responses, tests, and React
> copy so that "fixture vs live vs empty vs error vs DB-unavailable" never drifts
> between layers. When code and this document disagree, treat the disagreement
> as a bug in one of them and reconcile.

Companion docs: `12_Live_Adapter_Boundary.md` (which surface is promoted),
`08_API_Data_Source_Design.md` (adapters/DTOs), `.devmd/CURRENT_STATE.md`
(live progress).

## 1. The five snapshot states

Every product GET tab resolves to exactly one of five states. The discriminators
are the top-level `source` field and the per-tab `systemStatus.db` indicator.

| State | Trigger | `source` | `systemStatus.db` | Content shown |
|---|---|---|---|---|
| **fixture** | `X-FSO-Use-Fixture: 1` opt-in (visual baselines, demos) | `fixture` | `LIVE` | deterministic demo snapshot |
| **live** | DB reachable + rows exist | `live` | `LIVE` | real DB read model |
| **live-empty** | DB reachable, but the needed rows/account are absent | `live` | `LIVE` | explicit "no data yet" narrative, empty evidence |
| **live-error** | DB reachable, but building the read model raised | `live` | `LIVE` | explicit error narrative (exception **class name only**) |
| **db-unavailable** | `session is None` — no DB configured or unreachable | `fixture` | `MISSING` | fixture shape, labeled DB-unavailable |

### 1.1 Resolution order (per GET route)

```text
if X-FSO-Use-Fixture header truthy:      -> fixture        (db stays LIVE)
elif get_session_scope() is None:        -> db-unavailable (mark_db_unavailable -> db=MISSING)
elif required rows/account are absent:   -> live-empty      (source=live)
elif building the live read model raises:-> live-error      (source=live, detail=ExcClass)
else:                                    -> live
```

- `fixture` and `db-unavailable` both carry `source="fixture"`; they are
  distinguished by `systemStatus.db` (`LIVE` vs `MISSING`).
- `live`, `live-empty`, and `live-error` all carry `source="live"`; they are
  distinguished by their narrative + `dataState`.
- **No state ever fills a reachable-DB gap with fixture content** (Slice 80).
  Fixtures appear only for the explicit opt-in and the fully-offline path.

### 1.2 Helpers that implement the model

- `api/dependencies.py::get_session_scope` — yields a session or `None`.
- `api/dependencies.py::mark_db_unavailable(payload)` — stamps
  `systemStatus.db="MISSING"` on the offline fixture (Slice 82).
- Per-tab `_empty_live_response` / `_error_live_response` builders — explicit
  live-empty / live-error payloads (Slice 80; `risk_firewall`, `mission_control`,
  `news_intelligence`, `trade_memory`).

### 1.3 db-unavailable: current vs target

Slice 82 added the **label** (`db="MISSING"`) but the offline body is still the
deterministic fixture *shape* (so the cockpit renders offline). The label closes
the worst confusion (a live pill over a dead DB), but the body still shows sample
numbers. **Target (open):** an explicit minimal "connect a database" content
state — either a distinct per-tab body or a shared React banner keyed on the
`source="fixture"` + `db="MISSING"` signature — so a DB outage is never read as
real sample data. Tracked in `.devmd/CURRENT_STATE.md` Next Useful Slices.

## 2. Field contract

### 2.1 Top-level (all ten v4.2 tabs)

| Field | Type | Meaning |
|---|---|---|
| `source` | `"fixture" \| "live"` | Provenance of the response **content**. |
| `systemStatus.db` | `"LIVE" \| "MISSING"` | Per-tab DB indicator. `MISSING` only on the db-unavailable path. |
| `systemStatus.mode` | `"READ_MODE"` | Always read-only; no execution endpoint exists. |
| `systemStatus.guardCount` | `int` | Active guard/alert count at snapshot time. |
| `safetyCaption` | `str` | Descriptive disclaimer; never execution wording. |

`dataCompleteness` MUST NOT appear on a product tab — it is owned solely by
`/api/system-status` (enforced by the v4.2 contract test).

### 2.2 `/api/system-status` (operations contract)

Owns freshness and completeness for the whole cockpit; the global OS status bar
reads from here.

| Field | Type | Meaning |
|---|---|---|
| `dbStatus` | `"LIVE" \| "MISSING"` | DB reachability (SELECT 1). |
| `source` | `"fixture" \| "live"` | `live` when DB reachable, else `fixture`. |
| `dataCompleteness` | `"complete" \| "partial" \| "missing"` | `complete` = no stale flags, `partial` = some datasets missing, `missing` = DB unavailable. |
| `staleFlags` | `list[str]` | e.g. `db_unavailable`, `market_missing`, `news_missing`. |
| `latest*At` | `str \| null` | Newest stored timestamp per dataset. |
| `protocolAvailability` | `AVAILABLE \| NOOP \| UNAVAILABLE` | Whether each System Ops protocol can run. |

### 2.3 Per-tab `dataState` vocabularies

Coverage (Market Kernel, Symbol Lab, Analysis Workspace — shared via
`api/coverage.py`, Slice 83):

| Field | Values | Meaning |
|---|---|---|
| `coverageLevel` | `COMPLETE \| PARTIAL \| SPARSE \| EMPTY` | Stored-bar / indicator sufficiency. |
| `evidenceCoveragePercent` | `0–100` | `min(bars/20,1)*70 + indicator(30/15/0)`. |
| `missingSummary` | `str` | Graded copy; COMPLETE line carries a per-tab domain label. |

`coverageLevel` ladder (threshold `INDICATOR_WARMUP_BARS = 20`):

```text
bar_count <= 0                      -> EMPTY
bar_count < 20                      -> SPARSE
indicator not AVAILABLE             -> PARTIAL
else                                -> COMPLETE
```

Freshness (Control Room — Slice 72/75/78):

| Field | Values | Meaning |
|---|---|---|
| `marketFreshnessStatus` / `catalystFreshnessStatus` / `watchlistFreshnessStatus` / `railFreshnessStatus` | `FRESH \| STALE \| MISSING` | Per-rail + aggregate freshness. |
| `marketStaleAfterDays` / `watchlistStaleAfterDays` | `int` | Active staleness thresholds (settings contract). |
| `railFreshnessNote` | `str` | Latest rail timestamps + active policy (`stale > Nd`). |

`FRESH/STALE/MISSING` rule: `MISSING` when no timestamp; `STALE` when the
observed date is older than `generated_at - stale_after_days`; else `FRESH`.

Evaluation (Risk Firewall): `evaluationSource` (`fixture|live`),
`evaluationStatus` (`PASS|WARN|FAIL|BLOCKED|INFO` — note: live-empty/error use
`INFO`, since the enum has no MISSING/ERROR member), plus guard counts.

Chart/indicator (Market Kernel, Symbol Lab): `chartStatus` (`OK|PARTIAL|MISSING`),
`chartEvidence` (`stored|provider_preview|missing|fixture`), `indicatorStatus`
(`AVAILABLE|PARTIAL|MISSING`).

## 3. Settings that change state thresholds

| Env var | Default | Effect |
|---|---|---|
| `FINSKILLOS_CONTROL_ROOM_STALE_AFTER_DAYS` | `3` | Base market/watchlist staleness threshold. |
| `FINSKILLOS_CONTROL_ROOM_MARKET_STALE_AFTER_DAYS` | base | Per-rail override (market). |
| `FINSKILLOS_CONTROL_ROOM_WATCHLIST_STALE_AFTER_DAYS` | base | Per-rail override (watchlist). |

`INDICATOR_WARMUP_BARS` (coverage threshold) is a module constant in
`api/coverage.py`, not yet env-configurable.

## 4. Drift guards (which test enforces what)

- `tests/test_api_v42_contract.py`
  - structural contract holds for **both** fixture and live (no header);
  - fixture **anchors** (judgment vocabulary + safety category) are pinned with
    `X-FSO-Use-Fixture`;
  - every one of the ten tabs honours the fixture override;
  - `dataCompleteness` never leaks onto a product tab.
- `tests/test_api_db_unavailable.py` — offline path stamps `db=MISSING` while the
  fixture override keeps `db=LIVE`.
- `tests/test_coverage.py` — shared coverage ladder / percent / graded copy.
- Per-tab `tests/test_api_<tab>.py` — live, live-empty, live-error shapes.

**Rule for new contributors:** when a tab's state behaviour changes, update this
document, the per-tab test, and the React copy in the same slice. Do not let one
layer describe a state that another layer no longer produces.

## 5. Glossary (quick reference)

- **fixture** — deterministic demo snapshot; only via `X-FSO-Use-Fixture` opt-in.
- **live** — content read from the local DB.
- **live-empty** — DB reachable, required rows absent; explicit, `source=live`.
- **live-error** — DB reachable, read raised; explicit, `source=live`, exception
  class name only (no stack/message).
- **db-unavailable** — no/unreachable DB (`session is None`); `source=fixture`,
  `db=MISSING`.
- **dataState** — per-tab structured evidence-state block (coverage / freshness /
  evaluation / chart, depending on the tab).
- **dataCompleteness** — `complete|partial|missing`; **system-status only**.
- **coverageLevel / evidenceCoveragePercent / missingSummary** — shared coverage
  vocabulary (`api/coverage.py`).
- **staleFlags** — system-status list of missing/stale dataset markers.
- **FRESH / STALE / MISSING** — per-rail freshness classification (Control Room).
- **coverage threshold** — `INDICATOR_WARMUP_BARS = 20`.
- **fixture override** — the `X-FSO-Use-Fixture: 1` header forcing fixture mode.
