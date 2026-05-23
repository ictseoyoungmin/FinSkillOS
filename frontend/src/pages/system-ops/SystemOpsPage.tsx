import { useQuery } from "@tanstack/react-query";
import { fetchSystemOps, runSystemOpsProtocol } from "@/features/system-ops/api";
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
          badge={payload.systemStatus.db}
          badgeTone="success"
          testId="system-health"
        >
          <p>API mode: {payload.systemStatus.mode}</p>
        </Panel>
        <Panel
          title="Migration Status"
          badge={payload.source}
          badgeTone="info"
          testId="migration-status"
        >
          <p>Fixture-first React cockpit through Slice 13.11.</p>
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
