import { Panel } from "@/shared/ui";
import { GuardCard } from "./GuardCard";
import type { GuardSummary } from "../types";

export interface GuardStackProps {
  guards: GuardSummary[];
}

export function GuardStack({ guards }: GuardStackProps) {
  return (
    <Panel
      title="Risk Firewall"
      badge="Live"
      badgeTone="info"
      testId="risk-firewall-summary"
    >
      {guards.map((guard) => (
        <GuardCard key={guard.name} guard={guard} />
      ))}
    </Panel>
  );
}
