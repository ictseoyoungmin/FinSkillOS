import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchSystemOps,
  fetchSystemStatus,
  runSystemOpsProtocol,
} from "@/features/system-ops/api";
import { DataSourceStrip } from "@/features/system-ops/components/DataSourceStrip";
import { ProtocolCardItem } from "@/features/system-ops/components/ProtocolCardItem";
import type {
  WorkerCycleRecord,
  WorkerStatusSummary,
} from "@/features/system-ops/types";
import { systemOpsFixture } from "@/mocks/fixtures/systemOps.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  Panel,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import "./system-ops.css";

export function SystemOpsPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "worker">("overview");
  const { data, error } = useQuery({
    queryKey: ["system-ops"],
    queryFn: ({ signal }) => fetchSystemOps(signal),
    placeholderData: systemOpsFixture,
  });
  const { data: statusData } = useQuery({
    queryKey: ["system-status"],
    queryFn: ({ signal }) => fetchSystemStatus(signal),
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="system-ops-error"
        title="System Ops is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? systemOpsFixture;
  const dbBadgeTone = statusData?.dbStatus === "LIVE" ? "success" : "danger";
  const staleSummary = statusData
    ? summarizeStaleFlags(statusData.staleFlags)
    : {
        badge: "loading",
        tone: "info" as const,
        text: "Status endpoint loading.",
      };
  const latestSummary = statusData
    ? summarizeLatest(statusData)
    : "Freshness timestamps pending.";

  return (
    <div className="fso-system-ops" data-testid="system-ops-page">
      <SectionHeader eyebrow="FinSkillOS · Module" title="System Ops" />
      <div
        className="fso-system-ops-tabs"
        role="tablist"
        aria-label="System Ops sections"
      >
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "overview"}
          className={activeTab === "overview" ? "active" : ""}
          data-testid="system-ops-tab-overview"
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "worker"}
          className={activeTab === "worker" ? "active" : ""}
          data-testid="system-ops-tab-worker"
          onClick={() => setActiveTab("worker")}
        >
          Worker Status
        </button>
      </div>
      {activeTab === "overview" ? (
        <>
          <div className="fso-v42-topline">
            <JudgmentHeader judgment={payload.judgment} />
            <DriversPanel
              drivers={payload.drivers.map((driver) => ({
                label: driver.title,
                value: driver.score,
                detail: driver.note,
              }))}
            />
            <ConflictsPanel
              conflicts={payload.conflicts.map((conflict) => ({
                label: conflict.title,
                description: conflict.note,
              }))}
            />
          </div>
          <div className="fso-system-ops-evidence-row">
            <Panel
              title="System Health"
              badge={statusData?.dbStatus ?? payload.systemStatus.db}
              badgeTone={dbBadgeTone}
              testId="system-health"
            >
              <p>API mode: {statusData?.mode ?? payload.systemStatus.mode}</p>
              <p data-testid="system-status-summary">
                API {statusData?.apiStatus ?? "LIVE"} · source{" "}
                {(statusData?.source ?? payload.source).toUpperCase()} · completeness{" "}
                {(statusData?.dataCompleteness ?? "missing").toUpperCase()}
              </p>
            </Panel>
            <Panel
              title="Freshness Status"
              badge={staleSummary.badge}
              badgeTone={staleSummary.tone}
              testId="migration-status"
            >
              <p data-testid="system-freshness-status">{staleSummary.text}</p>
              <p>{latestSummary}</p>
            </Panel>
          </div>
          <div data-testid="system-ops-data-sources">
            <DataSourceStrip pills={payload.dataSources} />
          </div>
          <div data-testid="system-ops-protocols">
            <Panel
              title="Operational Protocols"
              badge="Safe"
              badgeTone="info"
              testId="protocol-cards"
            >
              <div className="fso-system-ops-protocol-list">
                {payload.protocols.map((protocol) => (
                  <ProtocolCardItem
                    key={protocol.key}
                    protocol={protocol}
                    onRun={() => runSystemOpsProtocol(protocol.key)}
                  />
                ))}
              </div>
              {payload.recentProtocolRuns.length > 0 ? (
                <div
                  className="fso-system-ops-history"
                  data-testid="recent-protocol-runs"
                >
                  {payload.recentProtocolRuns.map((run) => (
                    <p key={`${run.protocol}-${run.ranAt}`}>
                      {run.ranAt} · {run.protocol} · {run.status} · {run.dbStatus}
                    </p>
                  ))}
                </div>
              ) : null}
            </Panel>
          </div>
          <p
            className="fso-system-ops-caption"
            data-testid="system-ops-safety-caption"
          >
            {payload.safetyCaption}
          </p>
          <InterpretationPanel
            bullets={[
              payload.interpretation.verdict,
              payload.interpretation.whyItMatters,
              payload.interpretation.whatRemainsUncertain,
            ]}
          />
          <WatchpointsPanel
            watchpoints={payload.watchpoints.map((watchpoint) => ({
              label: watchpoint.title,
              description: watchpoint.note,
            }))}
          />
          <SafetyCaption>{payload.safetyCaption}</SafetyCaption>
        </>
      ) : (
        <WorkerStatusDashboard workerStatus={payload.workerStatus} />
      )}
    </div>
  );
}

function WorkerStatusDashboard({
  workerStatus,
}: {
  workerStatus: WorkerStatusSummary;
}) {
  const latest = workerStatus.recentCycles[0] ?? null;
  const components = latest
    ? [
        {
          label: "Market",
          status: latest.marketStatus,
          scope: latest.marketScope,
          value: "Bars",
        },
        {
          label: "News",
          status: latest.newsStatus,
          scope: latest.newsScope,
          value: "Feeds",
        },
        {
          label: "Indicators",
          status: latest.indicatorStatus,
          scope: latest.indicatorScope,
          value: "Signals",
        },
      ]
    : [
        { label: "Market", status: "MISSING", scope: "unknown", value: "Bars" },
        { label: "News", status: "MISSING", scope: "unknown", value: "Feeds" },
        {
          label: "Indicators",
          status: "MISSING",
          scope: "unknown",
          value: "Signals",
        },
      ];

  return (
    <div className="fso-worker-tab" data-testid="worker-status-dashboard">
      <Panel
        title="Worker Status"
        badge={workerStatus.status.toLowerCase()}
        badgeTone={workerBadgeTone(workerStatus.status)}
      >
        <div className="fso-worker-hero">
          <div
            className="fso-worker-status-orb"
            data-status={workerStatus.status}
            aria-hidden
          />
          <div className="fso-worker-hero-copy">
            <span>Latest cycle</span>
            <strong>{workerStatus.status}</strong>
            <small>{workerStatus.latestDetail}</small>
          </div>
          <div className="fso-worker-metrics">
            <WorkerMetric
              label="Started"
              value={workerStatus.latestStartedAt ?? "No cycle"}
            />
            <WorkerMetric
              label="Finished"
              value={workerStatus.latestFinishedAt ?? "No cycle"}
            />
            <WorkerMetric
              label="Duration"
              value={formatDuration(
                workerStatus.latestStartedAt,
                workerStatus.latestFinishedAt,
              )}
            />
            <WorkerMetric
              label="Recent"
              value={`${workerStatus.recentCycles.length} cycles`}
            />
          </div>
        </div>
      </Panel>

      <div className="fso-worker-grid">
        <Panel title="Cycle Components" badge="Read model" badgeTone="info">
          <div className="fso-worker-components">
            {components.map((component) => (
              <div
                className="fso-worker-component"
                data-status={component.status}
                key={component.label}
              >
                <span>{component.label}</span>
                <strong>{component.status}</strong>
                <small>{component.value} · {component.scope}</small>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Recent Cycle Trace" badge="5 latest" badgeTone="neutral">
          {workerStatus.recentCycles.length > 0 ? (
            <div className="fso-worker-trace" data-testid="worker-cycle-trace">
              {workerStatus.recentCycles.map((cycle) => (
                <WorkerCycleRow
                  key={`${cycle.startedAt}-${cycle.finishedAt}`}
                  cycle={cycle}
                />
              ))}
            </div>
          ) : (
            <div className="fso-worker-empty">
              No worker cycle has been recorded.
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function WorkerMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="fso-worker-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function WorkerCycleRow({ cycle }: { cycle: WorkerCycleRecord }) {
  return (
    <div className="fso-worker-cycle-row" data-status={cycle.status}>
      <div className="fso-worker-cycle-time">
        <strong>{cycle.status}</strong>
        <span>{cycle.startedAt}</span>
      </div>
      <div className="fso-worker-cycle-bars" aria-label="Cycle component status">
        <span data-status={cycle.marketStatus}>Market</span>
        <span data-status={cycle.newsStatus}>News</span>
        <span data-status={cycle.indicatorStatus}>Indicators</span>
      </div>
      <div className="fso-worker-cycle-meta">
        <span>{formatDuration(cycle.startedAt, cycle.finishedAt)}</span>
        <span>{cycle.timeframe}</span>
        <span>{cycle.marketScope}</span>
      </div>
    </div>
  );
}

function workerBadgeTone(
  status: string,
): "info" | "success" | "warning" | "danger" {
  if (status === "OK") {
    return "success";
  }
  if (status === "ERROR") {
    return "danger";
  }
  if (status === "NOOP") {
    return "warning";
  }
  return "info";
}

function formatDuration(start: string | null, finish: string | null): string {
  if (!start || !finish) {
    return "Pending";
  }
  const startedAt = Date.parse(start);
  const finishedAt = Date.parse(finish);
  if (Number.isNaN(startedAt) || Number.isNaN(finishedAt)) {
    return "Unknown";
  }
  const seconds = Math.max(0, Math.round((finishedAt - startedAt) / 1000));
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function summarizeStaleFlags(flags: string[]): {
  badge: string;
  tone: "info" | "success" | "warning";
  text: string;
} {
  if (flags.length === 0) {
    return {
      badge: "fresh",
      tone: "success",
      text: "No stale data flags reported by the operations contract.",
    };
  }
  return {
    badge: `${flags.length} stale`,
    tone: "warning",
    text: `Stale flags: ${flags.slice(0, 3).join(", ")}${
      flags.length > 3 ? " ..." : ""
    }`,
  };
}

function summarizeLatest(status: {
  latestPortfolioSnapshotAt: string | null;
  latestMarketBarAt: string | null;
  latestIndicatorAt: string | null;
  latestRegimeAt: string | null;
  latestNewsAt: string | null;
  latestEventAt: string | null;
}): string {
  return [
    `portfolio ${status.latestPortfolioSnapshotAt ?? "missing"}`,
    `market ${status.latestMarketBarAt ?? "missing"}`,
    `indicator ${status.latestIndicatorAt ?? "missing"}`,
    `regime ${status.latestRegimeAt ?? "missing"}`,
    `news ${status.latestNewsAt ?? "missing"}`,
    `event ${status.latestEventAt ?? "missing"}`,
  ].join(" · ");
}
