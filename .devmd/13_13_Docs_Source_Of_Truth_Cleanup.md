# 13.13 — Source-of-Truth Cleanup Before Operations

## Goal

Align the written project entry points with the current architecture
before Slice 14 starts. FinSkillOS is no longer a Streamlit-first MVP:
the product surface is now a FastAPI read-only adapter plus a Vite React
v4.2 Evidence-to-Judgment cockpit, with Streamlit retained only as a
debug / admin surface.

## Why this slice exists

The codebase has moved faster than several documents. The current source
of truth is distributed across:

```text
.devmd/13_11_UI_Completeness_Parity.md
frontend/e2e/visual/README.md
frontend/src/
api/
prototypes/ui/enhanced_dashboard_mockup/v4_2/
```

Older entry points still reference the v3.3 mockup as the latest UI
target or describe deployment as Local Streamlit + Docker Postgres. That
will confuse Slice 14 unless corrected first.

## Scope

Allowed:

```text
- Update README quickstart order so React/FastAPI/Postgres is the main
  product path and Streamlit is clearly debug/admin.
- Update docs/v2_1/CONTEXT_INDEX.md so v4.2 mockup + React implementation
  + Playwright visual gate are the current UI references.
- Rewrite .devmd/14_Deployment_Operations.md so it targets the current
  React/FastAPI/Postgres structure.
- Add a historical-status note to docs/v2_1/10_Deployment_Operations.md
  if it still describes the old Streamlit-first deployment target.
- Preserve older v2.1 design docs as background references rather than
  rewriting the entire docs tree.
```

Not allowed:

```text
- Add brokerage, order, trade execution, or direct buy/sell endpoints.
- Replace the deterministic v4.2 fixture-first UI baseline with live
  adapters.
- Remove Streamlit; keep it as debug/admin until a later explicit slice.
- Delete historical prototypes or old design docs.
```

## Completion

```text
Status: DONE
Updated:
- README.md
- .devmd/README.md
- docs/v2_1/CONTEXT_INDEX.md
- docs/v2_1/10_Deployment_Operations.md
- .devmd/14_Deployment_Operations.md

Notes:
- React/FastAPI is now documented as the primary product cockpit.
- Streamlit is documented as debug/admin only.
- Slice 14 now starts from local operations, fixture/live mode boundaries,
  health contracts, backups, migrations, and visual gate operations.
```
