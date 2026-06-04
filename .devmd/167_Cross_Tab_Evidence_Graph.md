# 167 — Cross-tab Evidence Graph (Phase 4)

**Status:** Done. Read-only. The aggregating interpretation layer — links the
regime / risk / events / portfolio read models into one descriptive graph.

Control Room already assembles all four read models in its live path
(`build_control_room_view_model` + `build_event_radar_view_model`). This slice
composes them into an evidence graph (nodes + cross-references) without
re-computing anything.

## Implemented

### API
- `ControlRoomResponse` gains `evidence_graph: EvidenceGraph | None`. Schemas:
  `EvidenceNode` (`key regime|risk|events|portfolio`, label, state, tone, drivers),
  `EvidenceLink` (`source`, `target`, `relation`), `EvidenceGraph`
  (nodes + links + summary).
- `_evidence_graph(vm, event_vm)` builds (live, account present):
  - **Regime** node — regime · risk_level, tone by risk level, top positive +
    risk factor.
  - **Risk Firewall** node — overall status + flagged count, top flagged guards.
  - **Catalyst Watch** node — high-risk / upcoming counts, top high-risk titles.
  - **Portfolio** node — position count, largest position, over-limit tickers.
  - **Links** derived from real flags: regime→risk (elevated regime risk),
    portfolio→risk (concentration), events→portfolio (events touch holdings),
    events→risk (high-exposure events). `None` when no account; absent in fixtures.

### Frontend
- `EvidenceGraphPanel` on Control Room (below the 3 columns): a node grid
  (tone-bordered cards with drivers) + a link list ("A → B: relation") + summary.
  Rendered only when `evidenceGraph` has nodes → fixture render unchanged, so the
  Control Room visual baseline is intact.

## Tests (`tests/test_api_control_room.py`, +1 within the live mission test)
- the live read model exposes `evidenceGraph` with risk/events/portfolio nodes,
  a summary, and links whose source/target reference real node keys.

## Verification
- Offline: control-room + v42 + safety-language pytest PASS; ruff clean.
- Frontend: `tsc -b` + `vite build` + eslint clean (pre-existing warning only).
- Docker (rebuilt images): api pytest + ruff + web build.

## Notes
- No migration. Pure aggregation of already-assembled VMs; live-gated → no
  Playwright regen.
- Next: 168 Weekly Evidence Report (closes Phase 4).
