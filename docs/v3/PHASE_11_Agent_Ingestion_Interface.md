# Phase 11 — Agent Ingestion Interface (user↔agent)

Spec: [AGENT_INTERFACE_SPEC.md](AGENT_INTERFACE_SPEC.md) §Phase 11.

**Goal:** the natural front door. User pastes text or drops a screenshot of
holdings / trades / watch changes → the configured LLM parses it into structured
proposals → a dry-run diff preview → user confirms → the agent applies real data
via the Phase-9 tools. Needs Phases 9 + 10.

## Flow

`INPUT (text / screenshot) → PARSE (provider → typed proposal) → PREVIEW (Phase-9
dry-run diff) → CONFIRM (all / per-section) → APPLY (Phase-9 tools) → receipt + audit`

## Candidate slices

- **Proposal schema + parser** — a typed `IngestionProposal`
  (`positions[]`, `trades[]`, `watch_changes[]`; **no order/execution field**).
  The provider returns it (constrained by JSON schema); off-schema → rejected.
  Tested with the echo/stub provider returning canned proposals (no LLM call).
- **Grounding read** — fetch current positions / trades / folders before parsing
  so proposals are diffs ("NVDA 10→12"), not blind duplicates.
- **Preview endpoint** — map the proposal to Phase-9 tool dry-runs → one diff
  (`+N positions, ~M updated, +K watch, T trade rows / I invalid`), per-row
  validity surfaced.
- **Apply endpoint** — on confirm, call the confirmed Phase-9 tools; record the
  receipt; return the refreshed read models.
- **Image ingestion** — route screenshots to a vision-capable provider; if the
  active provider lacks vision, prompt for text or a provider switch; image not
  persisted unless opted in.
- **Agent Inbox UI** — paste box + clipboard/file image drop, "Propose", the diff
  preview with per-section confirm, an applied-changes receipt.

## Dependencies

Phase 9 (tools) + Phase 10 (provider). Reuses the Phase-3 mutation endpoints under
the hood.

## Verification

- Offline integration: full parse→preview→apply with the echo provider + canned
  proposals; assert the dry-run doesn't mutate and confirm applies the exact diff;
  off-schema rejection; wording-scan on any drafted free text.
- Docker gate (rebuild api/web first).

## Constraints

- Descriptive bookkeeping only; confirm-gated; reversible (edit/delete). The
  schema has no execution field. Free text the agent drafts is guard-scanned.
