# FinSkillOS v2.1 Docs

This directory contains the source-of-truth design documents for the v2.1 OS-style rebuild.

Start with `CONTEXT_INDEX.md`, then open only the documents needed for the implementation slice you are working on.

Current operations addenda:

- `11_Scheduler_Refresh_Policy.md` — manual-first, cron-compatible refresh policy.
- `12_Live_Adapter_Boundary.md` — fixture/live promotion boundary.
  Includes the current `--adapter yahoo` market-bar refresh path and the
  remaining news-provider deferral.
