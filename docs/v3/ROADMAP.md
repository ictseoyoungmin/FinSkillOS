# FinSkillOS v3 Roadmap — Agent-Operated, Real-Data Cockpit (2026-06-05)

The v2.1 roadmap (Phases 0–6, slices ≤178) is **complete** — see
[`docs/ROADMAP.md`](../ROADMAP.md) and `CHANGELOG.md`. This v3 arc continues the
**same** slice sequence (next slice = **179**) and the **same hard constraints**:

- **Descriptive evidence-to-judgment only** — never buy/sell/order/price-direction
  output. The agent does **not** trade (see Phase 12).
- One slice = one commit on `main`, Docker-verified (rebuild images first — the
  158–164 stale-image lesson; see `.devmd/CURRENT_STATE.md` Validation Baseline).
- Offline-safe deterministic tests (no external API / network in tests).

## North star

Run the cockpit on **real data only**, operated through a **natural
agent↔user interface**: the user pastes text or drops a screenshot of their
holdings / trades / watchlist changes, and the agent collates it and applies it
to the database through internal tools — with a dry-run preview and explicit
confirmation. Keep the door open for a future brokerage API. The LLM provider
(Claude Code / Gemini API / local llama.cpp·vllm) is switchable from the Ops tab.

## Phases (7–12)

| Phase | Theme | Why now | Spec |
|---|---|---|---|
| **7** | Real-data integrity & honesty | Live mode must never present fixture/sample numbers as real; every card tagged live/derived/sample/empty | [REAL_DATA_AND_LAYOUT_SPEC](REAL_DATA_AND_LAYOUT_SPEC.md) |
| **8** | Layout / information-density redesign | Per-tab top→bottom audit; cut wasted vertical space, tighten hierarchy, responsive | [REAL_DATA_AND_LAYOUT_SPEC](REAL_DATA_AND_LAYOUT_SPEC.md) |
| **9** | Agent tool/API contract | A stable, documented, agent-callable tool registry over the existing mutation endpoints (dry-run → confirm, idempotent) | [AGENT_INTERFACE_SPEC](AGENT_INTERFACE_SPEC.md) |
| **10** | LLM provider abstraction + Ops switching | One provider interface + adapters (Claude Code / Gemini / local server), switchable + health-checked in Ops | [AGENT_INTERFACE_SPEC](AGENT_INTERFACE_SPEC.md) |
| **11** | Agent ingestion interface (user↔agent) | Paste text / drop screenshot → parse → dry-run preview → confirm → apply real data via Phase-9 tools | [AGENT_INTERFACE_SPEC](AGENT_INTERFACE_SPEC.md) |
| **12** | Brokerage / execution boundary (deferred, optional) | Read-only broker import first; execution out by default; if ever, last + conservative + paper-first | [AGENT_INTERFACE_SPEC](AGENT_INTERFACE_SPEC.md) §Execution |

Per-phase detail: `PHASE_07…12_*.md` in this directory.

## Ordering & dependencies

```
7 Real-data integrity ──┐
8 Layout redesign ──────┤  (7/8 are near-term, largely independent)
                        │
9 Agent tool contract ──┴──┐
10 LLM provider + Ops switch ──┐
                               │
11 Agent ingestion interface ──┘   (needs 9 + 10)
                               │
12 Brokerage / execution boundary (last, optional)
```

**Near-term (what the user asked for first):** Phase 7 (every card = real data or
explicitly marked) and Phase 8 (per-tab layout efficiency), since those are
direct UI/data-honesty work on the running cockpit. Then the agent stack (9 → 10
→ 11). Phase 12 stays last and optional by design.

## Standing principles carried into v3

- **Real data only** is a *contract*, not a vibe: see the data-authenticity tag
  in `REAL_DATA_AND_LAYOUT_SPEC.md`. Fixtures remain only for visual baselines
  (`X-FSO-Use-Fixture`) and offline tests — never surfaced as live.
- **Agent mutations are descriptive bookkeeping** (positions / trades / watch
  folders / snapshot baselines) — the exact surface Phase 3 already built
  (`/api/mission-control/*`, trade-memory import, collection-control). The agent
  adds a *natural-language front door* to those tools; it never invents a new
  power to trade.
- **LLM stays inside the boundary** established in slice 178
  (`finskillos/llm_explanation.py`): it narrates / parses / proposes; the
  forbidden-wording guard + confirm-gate keep judgment and direction out.

## Status

Planning docs only (this commit set). No slices started. Live queue and the
active phase will be tracked in `.devmd/CURRENT_STATE.md` once a phase begins
(awaiting "phase 7 진행" or the user's chosen entry point).
