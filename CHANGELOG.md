# Changelog

FinSkillOS ships in bounded **slices** (one commit each, `NN — Title`). This file
groups them into versioned phases. Regenerate the slice list for a range with
`python scripts/release_notes.py --from <ref> --to <ref>` (or `./fsoctl.sh
release-notes`).

The product is descriptive throughout — market state, risk interpretation,
portfolio constraints, reflection support — never buy/sell directives or order
placement.

## v0.5 — Phase 5 · Personal deployment / packaging (169–173)

- **169** — Operator CLI / Bootstrap (`fsoctl.sh`): one entrypoint over docker
  compose (setup/up/down/status/logs/migrate/seed/refresh/backup/verify).
- **170** — Upgrade / migration safety check (`scripts/migration_safety_check.py`):
  DB revision vs code head, flags downgrade risk before an upgrade.
- **171** — Backup-restore drill (`scripts/backup_verify.py` + `fsoctl.sh drill`):
  verifies a dump is complete and restorable; documented full restore drill.
- **172** — Local data-dir policy + release profile: `web-release` nginx static
  serve (`:8080`), `scripts/data_dir_report.py`, `.env.example` data/backup policy.
- **173** — Versioned release notes / CHANGELOG (this file + `release_notes.py`).

## v0.4 — Phase 4 · Interpretation engine (163–168)

Link evidence across tabs (descriptive, read-only). Risk-guard driver attribution ·
regime explanation v2 · event/news/position linkage scoring · portfolio
constraint summary v2 · cross-tab evidence graph · weekly evidence report.

## v0.3 — Phase 3 · Portfolio / journal real-use input (157–162)

Position reconciliation · portfolio manual entry (CRUD) · portfolio CSV
import/export · trade import CSV · weekly-review period navigation · journal
templates / review prompts.

## v0.2 — Phase 2 · Data trust / provider resilience (151–156)

Provider health dashboard · market-data provenance audit · indicator/bar invariant
dashboard · feed-coverage diagnostics · data-repair protocol · stale-RUNNING job
reaper.

## v0.1 — Phase 1 · Daily operating loop (145–150)

Operations runbook · worker queue visibility/recovery · refresh result explanation ·
provider retry/backoff · runtime settings change history · collection-control copy.

## v0.0 — Foundations through Phase 0 (≤144)

Domain/service/DB core, regime engine, risk guards, the v4.2 Evidence-to-Judgment
React cockpit, folder-driven collection control, and stabilization. Full
per-slice history: `.devmd/COMPLETED_SLICES.md` and `.devmd/<NN>_*.md`.
