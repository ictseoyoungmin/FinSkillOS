import { useQuery } from "@tanstack/react-query";
import { fetchSystemOps, runSystemOpsProtocol } from "@/features/system-ops/api";
import { DataSourceStrip } from "@/features/system-ops/components/DataSourceStrip";
import { ProtocolCardItem } from "@/features/system-ops/components/ProtocolCardItem";
import { systemOpsFixture } from "@/mocks/fixtures/systemOps.fixture";
import { EmptyState, Panel, SectionHeader } from "@/shared/ui";
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
      <DataSourceStrip pills={payload.dataSources} />
      <Panel
        title="Operational Protocols"
        badge="Safe"
        badgeTone="info"
        testId="system-ops-protocols"
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
      <p
        className="fso-system-ops-caption"
        data-testid="system-ops-safety-caption"
      >
        {payload.safetyCaption}
      </p>
    </div>
  );
}
