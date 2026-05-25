import { useQuery } from "@tanstack/react-query";
import {
  fetchSystemOps,
  fetchSystemStatus,
  runSystemOpsProtocol,
} from "@/features/system-ops/api";
import { DataSourceStrip } from "@/features/system-ops/components/DataSourceStrip";
import { ProtocolCardItem } from "@/features/system-ops/components/ProtocolCardItem";
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
            {(statusData?.source ?? payload.source).toUpperCase()}
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
    </div>
  );
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
}): string {
  return [
    `portfolio ${status.latestPortfolioSnapshotAt ?? "missing"}`,
    `market ${status.latestMarketBarAt ?? "missing"}`,
    `indicator ${status.latestIndicatorAt ?? "missing"}`,
    `regime ${status.latestRegimeAt ?? "missing"}`,
  ].join(" · ");
}
