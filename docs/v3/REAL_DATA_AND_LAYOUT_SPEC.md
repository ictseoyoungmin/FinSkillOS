# Real-Data Integrity & Layout Spec (v3)

> Living spec. Created 2026-06-05. Covers Phases 7–8 of `docs/v3/ROADMAP.md`.

The 10 tabs (left→right in the cockpit): **Control** (control-room), **Kernel**
(market-kernel), **Analysis** (analysis-workspace), **Symbol** (symbol-lab),
**Risk** (risk-firewall), **Mission** (mission-control), **News**
(news-intelligence), **Catalyst** (catalyst-watch / event-radar), **Memory**
(trade-memory), **Ops** (system-ops).

---

## Phase 7 — Real-data integrity & honesty

**Goal:** in live mode, the cockpit shows **only real data**, and any value that
is not a live DB fact is *explicitly marked* (derived / sample / empty). No
fixture number is ever presented as if it were real.

### What already exists (build on it)

- `source: "fixture" | "live"` on every payload; the
  `X-FSO-Use-Fixture` opt-in and `session is None` → db-unavailable are the only
  two honest fixture paths (slice 80). Live-empty / live-error are explicit
  states, never fixture substitutes.
- The **state vocabulary** (`docs/v2_1/13_State_Vocabulary_And_Data_Source_Contract.md`):
  source(live/fixture), db(LIVE/MISSING/UNAVAILABLE), freshness(FRESH/STALE/
  MISSING), coverage. Phase 4 added per-card attribution (guard / regime /
  event evidence) that is live-gated (empty in fixtures).

### The gap to close

Some cards still render **placeholder/derived** content without saying so when
live data is thin (e.g. a fixture-shaped panel showing through, a computed value
indistinguishable from a stored one, captions that read the same whether the row
is real or sample). The screenshots show the cockpit running fully live
(`DATA SOURCE LIVE`), but the audit must prove every visible element is one of:

| Tag | Meaning | Rule |
|---|---|---|
| **LIVE** | a stored DB fact | shown as-is |
| **DERIVED** | computed from live facts (e.g. weight %, reconciliation) | shown, labelled derived where ambiguous |
| **SAMPLE** | fixture / seeded sample | **only** in fixture mode; never in live |
| **EMPTY** | no data yet | explicit empty-state, not a zero masquerading as a value |

### Work

1. **Audit pass (per tab):** enumerate every card/element and classify it
   LIVE / DERIVED / SAMPLE / EMPTY. Produce a checklist (one slice per tab or a
   grouped audit slice) and fix any SAMPLE-in-live or unlabelled-DERIVED leak.
2. **Authenticity contract:** a small shared convention (data attribute / badge)
   so derived vs stored is visually distinguishable where it matters, and
   empty-states never show a fabricated number. Extends the existing source/state
   chips rather than inventing a parallel system.
3. **Seed honesty:** seeded sample rows (sample account / System folder) are
   legitimate *real* rows once a user keeps them, but the "Clear sample" path
   (slice 158) + an explicit "this is seeded sample data" marker let the user
   tell their data from the install seed.
4. **Acceptance:** a test/lint that asserts no live payload carries a fixture
   sentinel (e.g. `FIXTURE_TIMESTAMP`, known sample tickers) — extends the
   existing live-vs-fixture tests.

Candidate slices: a real-data audit doc/checklist, then per-tab honesty fixes
(group low-risk tabs), then the acceptance guard.

---

## Phase 8 — Layout / information-density redesign

**Goal:** per-tab top→bottom layout efficiency. The current screenshots show
**wasted vertical space** and long single-column stacks (e.g. Ops protocol
history, Control Room evidence sections) that force scrolling for content that
could sit denser.

### Audit method

For each of the 10 tabs, capture **top and bottom** and assess:

- **Vertical economy** — collapse tall empty gutters; promote dense tables over
  card-per-row stacks where the data is tabular.
- **Hierarchy** — the judgment/headline + the few key numbers should be visible
  without scrolling; detail (history, drilldowns) sits below or behind
  disclosure (`<details>`, already used by the Phase-4 attribution panels).
- **Consistency** — shared section header / panel / state-band components across
  tabs (most exist: `Panel`, `SectionHeader`, the evidence panels); reduce
  bespoke one-off layouts.
- **Responsiveness** — grids that reflow; no fixed-height dead zones.

### Constraints

- **Visual baselines.** Layout changes move the Playwright `@visual` baselines.
  Regenerating them needs browser binaries (env-blocked here — see CURRENT_STATE
  "Standing open"). Plan layout slices to either (a) run where Playwright browsers
  exist and regen, or (b) gate new structure so fixture renders are unchanged
  until a regen pass. Each layout slice must state which.
- **No behavior change** — layout/markup/CSS only; the read models and contracts
  are untouched, so the Phase-7 honesty work stays valid.

### Work

Per-tab slices (or grouped by similarity): a layout-audit doc with the
before/after intent per tab, then the redesign slices, then a visual-baseline
regen pass. Start with the tabs with the most obvious waste from the captures
(Ops history, Control Room evidence stack, Mission Control).

---

## Sequencing note

Phase 7 (honesty) and Phase 8 (layout) are largely independent and both operate
on the running cockpit, so they are the near-term entry points. Do the Phase-7
audit first (it's read-only analysis) so the layout pass doesn't entrench a card
that should have been an explicit empty-state.
