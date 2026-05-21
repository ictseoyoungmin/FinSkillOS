import { useQuery } from "@tanstack/react-query";
import { fetchRiskFirewall } from "@/features/risk-guards/api";
import { ActiveAlertsTable } from "@/features/risk-guards/components/ActiveAlertsTable";
import { GuardResultCard } from "@/features/risk-guards/components/GuardResultCard";
import { RiskProtocolPanel } from "@/features/risk-guards/components/RiskProtocolPanel";
import { riskFirewallFixture } from "@/mocks/fixtures/riskFirewall.fixture";
import { EmptyState, SectionHeader } from "@/shared/ui";
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
      <div className="fso-risk-firewall-grid">
        <GuardResultCard guards={payload.guards} />
        <ActiveAlertsTable alerts={payload.activeAlerts} />
        <RiskProtocolPanel
          protocol={payload.protocol}
          safetyCaption={payload.safetyCaption}
        />
      </div>
    </div>
  );
}
