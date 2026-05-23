import { useQuery } from "@tanstack/react-query";
import { fetchRiskFirewall } from "@/features/risk-guards/api";
import { ActiveAlertsTable } from "@/features/risk-guards/components/ActiveAlertsTable";
import { GuardResultCard } from "@/features/risk-guards/components/GuardResultCard";
import { RiskProtocolPanel } from "@/features/risk-guards/components/RiskProtocolPanel";
import { riskFirewallFixture } from "@/mocks/fixtures/riskFirewall.fixture";
import {
  ConflictsPanel,
  DriversPanel,
  EmptyState,
  InterpretationPanel,
  JudgmentHeader,
  SafetyCaption,
  SectionHeader,
  WatchpointsPanel,
} from "@/shared/ui";
import "./risk-firewall.css";

export function RiskFirewallPage() {
  const { data, error } = useQuery({
    queryKey: ["risk-firewall"],
    queryFn: ({ signal }) => fetchRiskFirewall(signal),
    placeholderData: riskFirewallFixture,
  });

  if (error && !data) {
    return (
      <EmptyState
        testId="risk-firewall-error"
        title="Risk Firewall is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  const payload = data ?? riskFirewallFixture;

  return (
    <div className="fso-risk-firewall" data-testid="risk-firewall-page">
      <SectionHeader
        eyebrow="FinSkillOS · Module"
        title="Risk Firewall"
      />
      <JudgmentHeader judgment={payload.judgment} />
      <div className="fso-risk-firewall-evidence-row">
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
      <div className="fso-risk-firewall-grid">
        <div data-testid="risk-firewall-guard-results">
          <GuardResultCard guards={payload.guards} />
        </div>
        <div data-testid="risk-firewall-active-alerts">
          <ActiveAlertsTable alerts={payload.activeAlerts} />
        </div>
        <div data-testid="risk-firewall-protocol">
          <RiskProtocolPanel
            protocol={payload.protocol}
            safetyCaption={payload.safetyCaption}
          />
        </div>
      </div>
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
