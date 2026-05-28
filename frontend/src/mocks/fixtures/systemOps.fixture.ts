import type { SystemOpsData } from "@/features/system-ops/types";

/**
 * Mirrors api/fixtures/system_ops.py. Wording is safe by contract;
 * no execution / order / buy / sell phrasing appears anywhere.
 */
export const systemOpsFixture: SystemOpsData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  judgment: {
    eyebrow: "SYSTEM TRUST JUDGMENT",
    title: "Local System Usable",
    accent: "with Partial Data",
    summary:
      "Core protocols are available in read mode while several data sources remain fixture-first.",
    confidence: 69,
  },
  drivers: [
    { score: "6", title: "Protocols", note: "Operational cards are available for deterministic local workflows." },
    { score: "Fixture", title: "Data layer", note: "Market, event, and news stores remain fixture-first." },
    { score: "Read", title: "Mode", note: "The system exposes operational protocols only." },
  ],
  conflicts: [
    { title: "Usable system vs fixture data", note: "The cockpit can run locally, but source freshness is limited." },
    { title: "Protocol actions vs trading actions", note: "Operational buttons do not create brokerage workflows." },
  ],
  interpretation: {
    verdict: "Local System Usable with Partial Data is the current trust read.",
    whyItMatters:
      "The page explains data-source status and safe operational protocols before a run.",
    whatRemainsUncertain:
      "Live adapter state and last-run timestamps can change the confidence level.",
  },
  watchpoints: [
    { title: "Fixture source", note: "Review data-source pills before relying on freshness." },
    { title: "Protocol idempotency", note: "Read each idempotency note before running a protocol." },
    { title: "Container health", note: "Check API and database status if protocol results drift." },
  ],
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
      key: "refresh_market_data",
      title: "Refresh market bars",
      description:
        "Updates stored OHLCV bars for the configured focus universe. Product pages remain read-only snapshots.",
      idempotencyNote:
        "Idempotent · existing bars are upserted by ticker, timeframe, and timestamp.",
      buttonLabel: "Refresh stored bars",
      confirmLabel: "Refresh stored bars",
      tone: "success",
      lastRunAt: null,
    },
    {
      key: "refresh_news",
      title: "Refresh news feeds",
      description:
        "Reads configured RSS or Atom feeds and stores article metadata plus short summaries for News Intelligence.",
      idempotencyNote:
        "Idempotent · existing articles are upserted by URL; full article bodies are not stored.",
      buttonLabel: "Refresh news metadata",
      confirmLabel: "Refresh news metadata",
      tone: "info",
      lastRunAt: null,
    },
    {
      key: "calculate_indicators",
      title: "Calculate indicators",
      description:
        "Computes descriptive technical snapshots from stored bars. No provider request is made during this protocol.",
      idempotencyNote:
        "Idempotent · latest snapshots are upserted by ticker, timeframe, and snapshot time.",
      buttonLabel: "Calculate indicators",
      confirmLabel: "Calculate indicators",
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
      title: "Seed event catalog",
      description:
        "Loads the deterministic Slice-11 event catalog through the System Ops ingestion boundary. Catalyst Watch stays read-only.",
      idempotencyNote:
        "Idempotent · existing rows are skipped by title; date statuses remain TENTATIVE / SPECULATIVE / WINDOW.",
      buttonLabel: "Seed event catalog",
      confirmLabel: "Seed event catalog",
      tone: "info",
      lastRunAt: null,
    },
  ],
  recentProtocolRuns: [],
  workerStatus: {
    status: "MISSING",
    cadenceStatus: "MISSING",
    latestStartedAt: null,
    latestFinishedAt: null,
    expectedNextCycleAt: null,
    latestDetail: "No worker cycle has been recorded.",
    cadenceDetail: "Worker cadence cannot be assessed until a cycle exists.",
    recentCycles: [],
  },
  dataSources: [
    {
      label: "Database",
      status: "FIXTURE",
      detail: "Fixture-first in Slice 13.8 · live DB optional.",
    },
    {
      label: "Market / Indicators",
      status: "FIXTURE",
      detail: "Stored bar refresh and indicator calculation are available.",
    },
    {
      label: "News / Event Stores",
      status: "FIXTURE",
      detail: "RSS refresh and System Ops event ingestion protocols available.",
    },
    {
      label: "Mode",
      status: "LIVE",
      detail: "Read mode · operational protocols only.",
    },
  ],
  safetyCaption: "Operational protocols only — no trading actions.",
};
