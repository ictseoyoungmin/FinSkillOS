# Phase 10 — LLM Provider Abstraction + Ops Switching

Spec: [AGENT_INTERFACE_SPEC.md](AGENT_INTERFACE_SPEC.md) §Phase 10.

**Goal:** one `LLMProvider` interface + adapters (Claude Code / Gemini API / local
llama.cpp·vllm server / offline echo), switchable from the Ops tab with per-
provider config + health check. Extends the slice-178 `Explainer` boundary.

## Candidate slices

- **Provider interface + echo adapter** — `finskillos/llm/provider.py`
  (`LLMProvider.complete(messages, *, tools?, images?) -> Response`,
  capability flags `supports_images`/`supports_tools`) + `registry.build_provider`
  (env `FINSKILLOS_LLM_PROVIDER`, default `echo`) + offline `echo` stub. The
  178 narration boundary routes through this. Tests use echo only.
- **Local OpenAI-compatible adapter** — `adapters/local_openai.py` for
  `llama.cpp --server` / vllm (`FINSKILLOS_LOCAL_LLM_BASE_URL`, model id);
  injectable HTTP sender so tests never touch the network.
- **Gemini adapter** — `adapters/gemini.py` (`FINSKILLOS_GEMINI_API_KEY`, model);
  injectable client; offline-tested.
- **Claude Code adapter** — `adapters/claude_code.py` (CLI / Agent SDK when
  available); capability-detected; offline-tested via a stub.
- **Ops "LLM Provider" panel** — current provider + health, a selector, per-
  provider config (key ref / base URL / model), "Test connection". Switch via the
  runtime-settings overlay (no restart).

## Dependencies

Extends `finskillos/llm_explanation.py` (178). Independent of Phase 9; both are
prerequisites for Phase 11.

## Verification

- Offline: provider resolution + each adapter via injected sender/client (no
  network); the echo fallback; ruff. Ops panel: tsc + vite build + eslint.
- Docker gate (rebuild api/web first).

## Constraints

- Provider used for parsing / narration / proposal — **never** trade decisions.
- Output reaching a descriptive surface is guard-scanned (178). No real API /
  network in tests. Keys are config refs, never committed.
