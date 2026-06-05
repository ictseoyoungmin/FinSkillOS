# FinSkillOS v3 — Agent-Operated, Real-Data Cockpit

Planning docs for the v3 arc (Phases 7–12), continuing the same slice sequence
(next = 179) and constraints as v2.1 (descriptive-only; one slice = one
Docker-verified commit; offline-safe tests).

- [`ROADMAP.md`](ROADMAP.md) — phases, ordering, north star.
- [`AGENT_INTERFACE_SPEC.md`](AGENT_INTERFACE_SPEC.md) — agent tool contract,
  LLM provider abstraction + Ops switching, ingestion interface, brokerage /
  execution boundary (Phases 9–12).
- [`REAL_DATA_AND_LAYOUT_SPEC.md`](REAL_DATA_AND_LAYOUT_SPEC.md) — real-data
  honesty contract + per-tab layout efficiency (Phases 7–8).
- `PHASE_07…12_*.md` — per-phase breakdown with candidate slices.

**Theme.** Operate on real data only, entered through a natural agent↔user
interface (paste text / drop a screenshot → dry-run preview → confirm → applied
to the DB via internal tools), with a switchable LLM provider (Claude Code /
Gemini / local llama.cpp·vllm) and an open seam for a future brokerage API. The
agent never trades (Phase 12 keeps execution last, optional, and conservative).

Status: **planning only** — no slices started. The active phase + live queue move
into `.devmd/CURRENT_STATE.md` when work begins.
