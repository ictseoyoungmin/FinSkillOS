# Phase 7 — Real-Data Integrity & Honesty

Spec: [REAL_DATA_AND_LAYOUT_SPEC.md](REAL_DATA_AND_LAYOUT_SPEC.md) §Phase 7.

**Goal:** live mode shows only real data; everything else (derived / sample /
empty) is explicitly marked. No fixture number presented as real.

## Candidate slices (sequence)

- **179 — Real-data audit checklist.** Per-tab enumeration of every card/element →
  LIVE / DERIVED / SAMPLE / EMPTY, with the specific leaks to fix. Doc + a
  machine-checkable list. (Read-only analysis; no code change.)
- **180 — Authenticity contract (shared chip/attribute).** A small shared
  convention extending the existing source/state chips so DERIVED vs LIVE is
  distinguishable and EMPTY never shows a fabricated value. Live-gated so fixture
  baselines are unchanged.
- **181–18x — Per-tab honesty fixes.** Group low-risk tabs; fix any
  SAMPLE-in-live or unlabelled-DERIVED found in 179. One slice per tab or per
  small group.
- **Acceptance guard.** A test asserting no live payload carries a fixture
  sentinel (extends the live-vs-fixture tests).

## Dependencies

None — read-only audit first, then additive markers. Independent of Phase 8.

## Verification

- Offline: extend `tests/test_api_*` live-vs-fixture assertions; ruff.
- Frontend: tsc + vite build + eslint; chips live-gated → no visual regen needed
  for the marker work.
- Docker gate (rebuild api/web first).

## Constraints

- Descriptive-only. Seeded sample rows stay legitimate once kept, but are
  distinguishable from user data (slice-158 "Clear sample" + a seed marker).
