# 187 — LLM Provider Abstraction (v3 Phase 10)

**Status:** Done. The switchable provider layer beneath the Slice-178 explainer.
Backend only; the Ops API + UI switcher is the next slice.

## Implemented (`finskillos/llm/provider.py`)
- `LLMProvider` protocol (`kind`, `available()`, `complete(prompt, system)`) +
  `LLMResult` / `ProviderAvailability` / `ProviderSpec`.
- Four adapters:
  - **`EchoProvider`** — deterministic offline default (no model/network).
  - **`ClaudeCodeProvider`** — local `claude` CLI; injectable `runner`.
  - **`GeminiProvider`** — Gemini API; injectable HTTP `transport`; reads
    `FINSKILLOS_GEMINI_API_KEY`.
  - **`LocalOpenAIProvider`** — localhost OpenAI-compatible server (llama.cpp /
    vLLM); injectable `transport`; reads `FINSKILLOS_LOCAL_LLM_BASE_URL`.
- `PROVIDER_SPECS` + `provider_catalog()` — Ops-switcher metadata (label,
  description, default model, required config, **availability from config alone**,
  no network probe) + `build_provider(kind)` factory (env
  `FINSKILLOS_LLM_PROVIDER`; unknown/unset → echo).

## Offline-safety
- `echo` is the default and the only provider exercised in tests. The
  network/subprocess adapters take an **injectable** transport/runner, so unit
  tests never call out; `available()` reports readiness from config presence only.
- Provider switching is descriptive infrastructure — the descriptive-only output
  boundary still lives in `llm_explanation.narrate` and is unaffected by the
  active provider.

## Tests (`tests/test_llm_provider.py`, +8)
- echo determinism + offline; `build_provider` default/resolve/fallback; catalogue
  lists all four with config-only availability (gemini not-ready without a key, no
  probe); injected runner/transport for claude_code / gemini / local; bad response
  shape raises.

## Verification
- Offline: provider pytest PASS; ruff clean.
- Docker (rebuilt api image): provider pytest + ruff.

## Notes
- Next (188): `GET /api/agent/providers` (catalogue + active) + Ops tab switcher
  (persist the active provider in runtime settings). Then Phase 11 ingestion.
