# FinSkillOS v2.1 Docs

This directory contains the source-of-truth design documents for the v2.1 OS-style rebuild.

Start with `CONTEXT_INDEX.md`, then open only the documents needed for the implementation slice you are working on.

Current operations addenda:

- `11_Scheduler_Refresh_Policy.md` — manual-first, cron-compatible refresh policy.
- `12_Live_Adapter_Boundary.md` — fixture/live promotion boundary (all tabs
  promoted). Includes the current `--adapter yahoo` market-bar refresh path and
  the remaining news-provider deferral.
- `13_State_Vocabulary_And_Data_Source_Contract.md` — authoritative state
  glossary (fixture / live / live-empty / live-error / db-unavailable), field
  contract, thresholds, and drift-guard tests.
