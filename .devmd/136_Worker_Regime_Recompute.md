# 136 — Worker Recomputes Regime Each Cycle (AW-2)

**Status:** Done.

Fixes the Analysis Workspace trust bug where the headline **Regime Context drifts
stale** and contradicts the live evidence on the same screen.

## Root cause
The worker `run_cycle` refreshed bars → news → indicators every cycle but **never
recomputed the market regime**; the regime only updated when an operator clicked
the manual "Regime 재계산" System Ops protocol. So a regime snapshot froze in place
while bars kept updating. Confirmed live: latest regime snapshot was
`2026-06-01 PANIC/RED/92` ("VIX 공포 구간 30↑") while the VIX bars had been **15–16
for days** (06-02 = 16.26) and the tape was broadly bullish. A manual recompute
self-corrected to `RISK_ON_OVERHEAT/YELLOW/80` — i.e. the engine was right, it just
was never re-run.

## Fix
- `scripts/refresh_worker.py::run_cycle` recomputes the regime after the indicator
  step (`RegimeService.evaluate_today_regime(persist=True)`) and records a `regime`
  section in the cycle summary (`status`, `regime`, `riskLevel`, `decisionMode`,
  `confidence`). The regime reads indicator/bar snapshots, so it is gated on
  `regime_enabled AND indicator_enabled` — it runs for the full cycle and the
  `calculate_indicators` job, but is skipped after a market- or news-only job.
- New flag `FINSKILLOS_WORKER_REGIME_ENABLED` (default on) — added to the runtime
  allow-list (`finskillos/runtime_settings.py`), the Ops Worker settings UI, and
  `.env.example`. The master switch is honored (the gate uses the configured value,
  not a per-job override).

## Tests
- `tests/test_operations_scripts.py` (+2): a market+indicator `--once` cycle
  persists a `MarketRegime` row and a `regime: OK` summary section; a market-only
  cycle leaves `regime: SKIPPED` and writes no regime row.

## Verification
- Offline: ops-scripts + worker-jobs + system-ops + config tests PASS; ruff clean;
  frontend `npm run build` + `npm run lint` clean.
- Docker: api/worker/web images build; worker ops + system-ops pytest + ruff PASS.
- Live: rebuilt worker recompute on cycle → fresh regime snapshot.

## Note
- AW-3 (surface regime snapshot age + STALE marker on the card when older than the
  latest bar; coverage-messaging copy cleanup) remains as the next slice — useful
  defense for when live mode is off or the worker is down.
