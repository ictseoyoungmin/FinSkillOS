import { Panel } from "@/shared/ui";
import { GuardCard } from "./GuardCard";
import type { GuardSummary } from "../types";
import "./guard-result-card.css";

export interface GuardResultCardProps {
  guards: GuardSummary[];
}

/**
 * Risk Firewall "Guard Results" panel — lists every guard the Slice-06 ladder
 * evaluated. v3 Phase 8 (183): the guards lay out in a responsive 2-column grid
 * so the ladder is roughly half as tall and uses the column width, instead of a
 * single tall stack of full-width rows.
 */
export function GuardResultCard({ guards }: GuardResultCardProps) {
  return (
    <Panel
      title="Guard Results"
      badge="Active"
      badgeTone="info"
      testId="guard-result-cards"
    >
      <div className="fso-guard-result-grid">
        {guards.map((guard) => (
          <GuardCard key={guard.name} guard={guard} />
        ))}
      </div>
    </Panel>
  );
}
