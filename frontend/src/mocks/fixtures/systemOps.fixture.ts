import type { SystemOpsData } from "@/features/system-ops/types";

/**
 * Mirrors api/fixtures/system_ops.py. Wording is safe by contract;
 * no execution / order / buy / sell phrasing appears anywhere.
 */
export const systemOpsFixture: SystemOpsData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  protocols: [
    {
      key: "seed_sample_account",
      title: "Seed sample account",
      description:
        "Creates the default Main Trading Account and an initial portfolio snapshot used by the cockpit.",
      idempotencyNote:
        "Idempotent · reuses the existing account and snapshot when already present.",
      buttonLabel: "Seed sample data",
      confirmLabel: "Seed sample data",
      tone: "info",
      lastRunAt: null,
    },
    {
      key: "recompute_regime",
      title: "Recompute market regime",
      description:
        "Re-runs the regime interpretation pipeline over the stored indicator snapshots. Descriptive only.",
      idempotencyNote:
        "Idempotent · the latest stored regime is updated in place; no historical rows are removed.",
      buttonLabel: "Recompute interpretation",
      confirmLabel: "Recompute interpretation",
      tone: "info",
      lastRunAt: null,
    },
    {
      key: "run_risk_guards",
      title: "Run risk guards",
      description:
        "Re-evaluates the full guard ladder for the default account and refreshes the active alerts table.",
      idempotencyNote:
        "Idempotent · same-day alerts are refreshed in place instead of stacking new rows.",
      buttonLabel: "Refresh stored view",
      confirmLabel: "Run protocol",
      tone: "warning",
      lastRunAt: null,
    },
    {
      key: "seed_sample_events",
      title: "Seed sample events",
      description:
        "Loads the deterministic Slice-11 catalog of uncertain events. Status remains tentative / speculative / window.",
      idempotencyNote:
        "Idempotent · existing rows are skipped by title; no event is upgraded to CONFIRMED automatically.",
      buttonLabel: "Seed sample data",
      confirmLabel: "Seed sample data",
      tone: "info",
      lastRunAt: null,
    },
  ],
  dataSources: [
    {
      label: "Database",
      status: "FIXTURE",
      detail: "Fixture-first in Slice 13.8 · live DB optional.",
    },
    {
      label: "Market Bars",
      status: "FIXTURE",
      detail: "Stored data only · no automatic live refresh.",
    },
    {
      label: "News / Event Stores",
      status: "FIXTURE",
      detail: "Manual upsert and seed helpers available.",
    },
    {
      label: "Mode",
      status: "LIVE",
      detail: "Read mode · operational protocols only.",
    },
  ],
  safetyCaption: "Operational protocols only — no trading actions.",
};
