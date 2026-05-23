import { Panel } from "@/shared/ui";
import { GuardCard } from "./GuardCard";
import type { GuardSummary } from "../types";

export interface GuardResultCardProps {
  guards: GuardSummary[];
}

/**
 * Risk Firewall "Guard Results" panel — lists every guard the
 * Slice-06 ladder evaluated. Mirrors the v4.1 mockup `Guard Results`
 * column. Re-uses the shared `GuardCard` row so styling stays
 * consistent with the Control Room summary.
 */
export function GuardResultCard({ guards }: GuardResultCardProps) {
  return (
    <Panel
      title="Guard Results"
      badge="Active"
      badgeTone="info"
      testId="guard-result-cards"
    >
      {guards.map((guard) => (
        <GuardCard key={guard.name} guard={guard} />
      ))}
    </Panel>
  );
}
