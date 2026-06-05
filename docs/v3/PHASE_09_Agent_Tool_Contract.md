# Phase 9 — Agent Tool / API Contract

Spec: [AGENT_INTERFACE_SPEC.md](AGENT_INTERFACE_SPEC.md) §Phase 9.

**Goal:** a documented, schema'd, agent-callable **tool registry** over the
existing mutation endpoints, with uniform dry-run/confirm + audit. The agent can
only call declared tools; each is reversible/idempotent.

## Candidate slices

- **Tool registry skeleton** — `finskillos/agent/tools.py`: a registry of tools,
  each with a JSON-schema input + typed result + a `dry_run` capability flag.
  Read tools first (positions / trades / folders / regime / events) so the agent
  can ground proposals.
- **Write tools (wrap existing endpoints)** — `portfolio.upsert_position` /
  `delete_position` / `import_positions` / `set_snapshot_baseline`,
  `trades.import` / `append_entry`, `watch.add_ticker` / `remove_ticker` /
  `create_folder` / `delete_folder`. Each wraps the existing route; no new write
  power. Bulk tools expose the existing dry-run→confirm.
- **Agent surface** — `api/routes/agent.py` (or reuse) exposing the registry as a
  discoverable, schema-described list (`GET /api/agent/tools`) + an invoke path
  that enforces the schema and the confirm-gate.
- **Audit** — record each applied tool call (tool, input diff, who/when) via the
  System Ops protocol-history pattern.

## Dependencies

Builds directly on Phase 3 endpoints (`/api/mission-control/*`, trade-memory
import, collection-control) — all already shipped. No new schema/migration for
the wrappers.

## Verification

- Offline integration tests per tool (sqlite): dry-run does not mutate; confirm
  applies; schema rejects bad input; idempotent re-run.
- Docker gate (rebuild api first).

## Constraints

- Descriptive bookkeeping only — no order/execution tool. Brokerage import is a
  Phase-12 *read* adapter feeding the same `import_*` tools.
