# Agent Interface & LLM Provider Spec (v3)

> Living spec. Created 2026-06-05. Covers Phases 9–12 of `docs/v3/ROADMAP.md`.

## Problem

Entering real holdings, trades, and watchlist changes by hand (forms / CSV) is
tedious. The user wants a **natural front door**: paste text or drop a screenshot
of a brokerage statement / position list / trade confirmation, and have the agent
collate it and write it to the database as **real data** — with a preview and a
confirmation. The LLM that does the parsing must be **switchable** (Claude Code /
Gemini API / local server) and must stay strictly inside the descriptive boundary
(it parses and proposes; it never decides or trades).

## Non-negotiable boundaries

1. **No execution.** The agent never places orders. Mutations are descriptive
   bookkeeping only: positions, trades (journal), watch folders, snapshot
   baselines — the exact set Phase 3 already exposes. Brokerage *execution* is
   Phase 12, deferred and optional, paper-first, heavily gated.
2. **Confirm-gated, reversible.** Every agent-proposed change is a **dry-run
   preview** first; nothing is written until the user confirms. Writes reuse the
   existing idempotent endpoints, so they're re-runnable and individually
   reversible (edit/delete).
3. **LLM inside the slice-178 boundary.** The provider narrates / parses /
   proposes structured data. Free-text it emits that reaches a descriptive
   surface is scanned by `finskillos.llm_explanation` /
   `finskillos.guards.base.assert_no_forbidden_wording`. The LLM never outputs a
   buy/sell judgment.
4. **Real data only.** Applied values are the user's actual numbers. Nothing the
   agent writes is fixture/sample; see `REAL_DATA_AND_LAYOUT_SPEC.md`.

---

## Phase 9 — Agent tool/API contract

A documented, stable **tool registry** the agent calls. These wrap endpoints that
**already exist** (Phase 3 + collection control); Phase 9 makes them an explicit,
schema'd, agent-facing contract with uniform dry-run/confirm semantics.

| Tool | Wraps (existing) | Dry-run? |
|---|---|---|
| `portfolio.upsert_position` | `POST/PUT /api/mission-control/positions` | n/a (single, reversible) |
| `portfolio.delete_position` | `DELETE /api/mission-control/positions/{id}` | n/a |
| `portfolio.import_positions` | `POST /api/mission-control/import-positions` | **yes** (`?confirm=true`) |
| `portfolio.set_snapshot_baseline` | `PATCH /api/mission-control/snapshot` | n/a |
| `trades.import` | `POST /api/trade-memory/import` | **yes** (`?confirm=true`, atomic) |
| `trades.append_entry` | `POST /api/trade-memory/entries` | n/a |
| `watch.add_ticker` / `watch.remove_ticker` | collection-control folder CRUD | n/a |
| `watch.create_folder` / `watch.delete_folder` | collection-control CRUD | n/a |
| `reports.generate` | `scripts/generate_report.py` / report builder | read-only |

Contract requirements:

- **Schemas.** Each tool has a JSON-schema'd input + a typed result. The agent
  selects a tool + fills its schema; it cannot call an undeclared mutation.
- **Idempotency.** Imports upsert (positions) / append-atomic (trades) exactly as
  today, so re-running a confirmed proposal is safe.
- **Dry-run → confirm.** Bulk tools return a preview (`adds/updates/…`,
  per-row OK/INVALID) without writing; a second confirmed call applies. This is
  the existing 159/160 shape — the agent surfaces the preview to the user.
- **Audit.** Every applied agent action is recorded (who/what/when + the tool +
  the diff), reusing or extending the System Ops protocol-history pattern.
- **Read tools** (portfolio/positions/trades/regime/events read models) let the
  agent ground its proposals in current DB state before proposing a change.
- **Brokerage seam (extensibility).** The tool registry is provider-agnostic: a
  future `broker.import_positions` / `broker.import_trades` adapter implements the
  same `portfolio.import_positions` / `trades.import` contract, so adding a broker
  is a new read adapter, not a new mutation surface.

Delivery: a small `finskillos/agent/tools.py` registry + `api/routes/agent.py`
(or reuse existing routes) that exposes the registry as a discoverable,
schema-described surface; per-tool slices.

---

## Phase 10 — LLM provider abstraction + Ops switching

One interface, several adapters, switchable from the Ops tab. Extends the
slice-178 `Explainer` boundary into a richer `LLMProvider`.

```
finskillos/llm/
  provider.py        # LLMProvider protocol: complete(messages, *, tools?, images?) -> Response
  registry.py        # build_provider(name|settings) — env / runtime-settings driven
  adapters/
    claude_code.py   # Claude Code CLI / Agent SDK (default when available)
    gemini.py        # Gemini API (google-genai), key from settings
    local_openai.py  # OpenAI-compatible localhost server: llama.cpp / vllm
    echo.py          # offline deterministic stub (tests + no-provider fallback)
```

- **Selection** via runtime-settings (the existing `system_ops_settings` overlay)
  + env default `FINSKILLOS_LLM_PROVIDER` (`echo` default — offline-safe). Switch
  at runtime from **Ops → LLM Provider** (no restart), with per-provider config:
  - Claude Code: binary path / SDK availability.
  - Gemini: `FINSKILLOS_GEMINI_API_KEY`, model id.
  - Local: base URL (e.g. `http://localhost:8000/v1`), model id — works with
    `llama.cpp --server` and vllm's OpenAI-compatible server.
- **Capabilities** are declared per adapter (`supports_images`, `supports_tools`)
  so the ingestion flow degrades gracefully (text-only when vision is absent).
- **Health check** per provider in Ops (reachable? model responds to a ping?),
  surfaced like provider-health (Phase 2).
- **Boundary stays.** Provider output that reaches a descriptive surface is
  guard-scanned (178). The provider is used for parsing/narration/proposal — never
  to decide trades. Tests use the `echo`/stub adapter; **no real API or network in
  tests**.

Ops UI: a "LLM Provider" panel — current provider + status, a selector, per-
provider config fields (key refs, base URL, model), a "Test connection" button.

---

## Phase 11 — Agent ingestion interface (user↔agent)

The natural front door. Flow:

```
1. INPUT     User pastes text, or drops/【captures】 a screenshot (image), in an
             "Agent Inbox" surface (Ops tab or a global command surface).
2. PARSE     The configured LLM provider extracts structured proposals:
             positions[], trades[], watch_changes[] — grounded against current DB
             read models. Vision adapters read screenshots; text adapters read paste.
3. PREVIEW   The agent maps proposals to Phase-9 tool dry-runs and shows a single
             diff: "+2 positions, ~3 updated, +1 watch ticker, 4 trade rows
             (1 invalid)". Invalid rows are flagged with why.
4. CONFIRM   The user approves (all / per-section). Nothing is written until then.
5. APPLY     The agent calls the confirmed Phase-9 tools; the DB + dashboard
             update with real data. The action is audited.
```

Requirements:

- **Structured intermediate.** The provider returns a typed proposal object
  (not free prose) so the preview is deterministic and the apply is exact. A JSON
  schema constrains it; anything off-schema is rejected, not guessed.
- **Grounding.** Before proposing, the agent reads current positions / trades /
  folders so it can say "update NVDA 10→12" rather than blindly duplicating.
- **Image handling.** Screenshots are sent to a vision-capable provider; if the
  active provider lacks vision, the UI asks for text or to switch providers. No
  image is persisted beyond the ingestion request unless the user opts in.
- **Safety.** Proposals are descriptive bookkeeping only; the schema has no
  order/execution field (same shape constraint as
  `finskillos.llm_explanation.ExplanationRequest`). The apply path is the
  confirm-gated Phase-9 tools. Free text (e.g. a thesis the agent drafts) is
  wording-scanned.
- **Offline tests.** The ingestion pipeline is tested with the `echo`/stub
  provider returning canned proposals; the parse→preview→apply path is exercised
  without any LLM call.

UI: an "Agent Inbox" — paste box + file/clipboard image drop, a "Propose" button,
the diff preview with per-section confirm, and an applied-changes receipt.

---

## Phase 12 — Brokerage / execution boundary (deferred, optional)

Kept last and small by intent ("거래는 하지 않을 것이며 하더라도 가장 마지막에
보수적인 계약으로").

- **Read-only first.** A `BrokerAdapter` that *imports* positions / trades from a
  brokerage API into the same Phase-9 `portfolio.import_positions` /
  `trades.import` tools. No new write power; just another source feeding the
  existing descriptive bookkeeping.
- **Execution is out by default.** If ever added, it is:
  - **paper / simulation first**, behind an explicit, off-by-default capability
    flag, with a separate confirmation contract distinct from bookkeeping;
  - **descriptive-only elsewhere** — the rest of the cockpit never gains
    buy/sell language;
  - the **last** thing built, with its own spec slice before any code.

This phase has **no near-term slices**; it exists to keep the architecture honest
about where a broker would plug in and to reserve "execution" as a deliberate,
separate, conservative decision.

---

## Cross-cutting

- **Settings.** New env: `FINSKILLOS_LLM_PROVIDER` (+ per-provider keys/urls),
  `FINSKILLOS_GEMINI_API_KEY`, `FINSKILLOS_LOCAL_LLM_BASE_URL`. All documented in
  `.env.example`; provider switch also via the runtime-settings overlay.
- **Audit & reversibility.** Agent-applied changes are logged + individually
  reversible via the existing edit/delete endpoints.
- **Testing.** `echo`/stub provider + canned proposals; no network. Each tool +
  the ingestion pipeline gets offline integration tests. Docker gate after
  rebuild, as always.
