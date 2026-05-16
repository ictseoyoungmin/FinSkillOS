# Agent Work Instructions

This directory is for execution instructions, not source design.

Workflow:

1. Read `docs/v2_1/CONTEXT_INDEX.md`.
2. Open the source documents listed for the current task.
3. Implement inside `finskillos/`.
4. Keep v1 files in `legacy_v1/` unless explicitly asked to reuse or migrate them.
5. Do not mix v1 `engine/`, `ui/`, or `FinSkillOS_skills/` modules into the v2.1 package.
6. Avoid direct buy/sell recommendation features; keep outputs explanatory, risk-aware, and decision-support oriented.
