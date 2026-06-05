# 188 — Ops LLM Provider Switcher (v3 Phase 10)

**Status:** Done. Completes Phase 10 — the Ops tab can switch the active LLM
provider (Claude Code / Gemini / local / echo), persisted in runtime settings.

## Implemented

### Backend
- `finskillos/runtime_settings.py` — added `FINSKILLOS_LLM_PROVIDER` to the
  runtime-setting allow-list (so it persists + audits via the existing overlay).
- `api/schemas/agent.py` — `LLMProviderVM`, `AgentProvidersResponse` (active +
  catalogue + boundary), `ProviderSwitchRequest` (Literal kind → invalid is 422).
- `api/routes/agent.py`:
  - `GET /api/agent/providers` — catalogue (label / description / required config /
    config-derived readiness) + the active selection (env + DB override; falls back
    to `echo` when DB is unavailable).
  - `PATCH /api/agent/providers` — validates the kind, persists via
    `SystemOpsSettingsRepository.patch`, returns the refreshed catalogue. 503 if DB
    is unavailable.

### Frontend
- `features/agent/{types,api}.ts` + `components/LLMProviderSwitcher.tsx` — react-
  query card listing each provider with a Ready / Not-ready `OriginTag` + reason,
  an Active pill, and a "Use this provider" button (PATCH → cache update). Rendered
  in the System Ops **Runtime** tab above the runtime settings.

## Boundary
Switching changes only the narrator backend; the descriptive-only output boundary
stays enforced in `llm_explanation.narrate` regardless of provider (surfaced in
the response `boundary` + the UI footer).

## Tests (`tests/test_api_agent_providers.py`, +4)
- catalogue lists the four with a default active of `echo`; switch persists
  (PATCH → GET reflects `local`); invalid kind → 422; gemini not-ready without a
  key (config-only, no probe).

## Verification
- Offline: agent-providers + agent + provider pytest PASS; ruff clean; tsc + vite
  build + eslint clean.
- Docker (rebuilt api + web): those suites + web build.

## ⚠ Visual baselines
The Runtime tab gains the switcher card → its `@visual` baseline drifts; the user
regenerates.

## Notes
- Next: **Phase 11 — agent ingestion interface** (paste / screenshot → parse →
  preview → confirm → apply via the Phase-9 tools, dry-run first).
