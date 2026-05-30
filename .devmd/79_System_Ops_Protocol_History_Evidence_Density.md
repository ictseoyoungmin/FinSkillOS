# 79 — System Ops Protocol History Evidence Density

Date: 2026-05-30

## Goal

Render recent protocol-run `detailEvidence` in the System Ops history area.
Slice 76 already exposed structured `detailEvidence` on every
`ProtocolRunRecord` (preferring the API rows and falling back to the legacy
`detail` string). The history list, however, still showed only a one-line
`ranAt · protocol · status · dbStatus` summary, hiding the per-run evidence
that accumulates in the audit table. This slice surfaces that evidence as
compact chips under each run, reusing the result-card evidence derivation.

## Implemented

- Extracted the evidence-derivation logic into a shared module
  `frontend/src/features/system-ops/detailEvidence.ts`:
  - `parseProtocolDetail(detail)` — parse the legacy comma-separated
    `key=value` audit string (moved verbatim out of `ProtocolCardItem`).
  - `deriveProtocolEvidence(run)` — prefer structured `detailEvidence`, fall
    back to parsing `detail`, so both live records and older audit rows render.
- `ProtocolCardItem.tsx` now imports `deriveProtocolEvidence` and drops its
  local parser, keeping the immediate result card and the history list on one
  derivation path.
- `SystemOpsPage.tsx` history area now renders each run as a summary line plus
  a `dl` of evidence chips
  (`data-testid="recent-protocol-run-evidence-<protocol>"`) when evidence is
  present. The `recent-protocol-runs` container testid is unchanged.
- Added compact history-run / chip styling to
  `frontend/src/pages/system-ops/system-ops.css` (mirrors the result-card chip
  look).

## Tests added

- `frontend/e2e/risk-mission-ops.spec.ts`
  - `System Ops history renders structured detail evidence per run` —
    route-mocks `GET /api/system-ops` to inject two recent runs (one with
    structured `detailEvidence`, one with only a legacy `detail` string) and
    asserts the history area renders the structured chips for the first and
    the parsed `bars=120` chip for the second.

## Notes

- Frontend-only slice. No API/schema/fixture change was needed because the
  `detailEvidence` contract already ships on `recentProtocolRuns` (Slice 76),
  and the default fixture keeps `recentProtocolRuns` empty so the default
  System Ops visual baseline is unchanged.
- The legacy `detail` string remains the audit/DB-history source of truth; the
  chips are a presentation of it.
- Copy stays descriptive operational evidence only — no execution, order, or
  buy/sell wording was introduced.

## Verification

- `docker compose -f docker-compose.yml run --rm --no-deps web sh -c
  "npm run build && npm run lint"`
  ✅ build succeeds · lint clean (pre-existing Slice 13.6 react-refresh warning
  only)
- `docker compose -f docker-compose.yml build web`
- `docker compose -f docker-compose.yml up -d postgres api web`
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx
  playwright test e2e/risk-mission-ops.spec.ts -g "System Ops history renders"`
  ✅ passed
- `docker compose -f docker-compose.yml --profile e2e run --rm e2e npx
  playwright test e2e/risk-mission-ops.spec.ts --workers=1`
  ✅ passed (full Risk/Mission/System Ops spec, no regression)

## Known issues

- The pre-existing, environment-state
  `tests/test_api_system_ops.py::test_seed_sample_events_protocol_is_audited_and_preserves_uncertain_statuses`
  failure noted in Slices 77/78 persists on the local persistent postgres and
  is unrelated to this frontend-only slice.
