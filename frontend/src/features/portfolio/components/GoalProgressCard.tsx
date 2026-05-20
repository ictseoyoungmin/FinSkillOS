import { Panel } from "@/shared/ui";
import { formatKrw, formatPct } from "@/shared/lib/format";
import type { MissionProgress } from "../types";
import "./goal-progress-card.css";

export interface GoalProgressCardProps {
  mission: MissionProgress;
}

export function GoalProgressCard({ mission }: GoalProgressCardProps) {
  return (
    <Panel
      title="Mission Progress"
      badge={mission.phase}
      badgeTone="info"
      testId="mission-progress-card"
    >
      <div className="fso-mission-figure">
        <span className="fso-mission-percent">
          {formatPct(mission.progressPct)}
        </span>
        <span className="fso-mission-mode">{mission.goalMode}</span>
      </div>
      <div className="fso-mission-bar" aria-hidden>
        <span
          className="fso-mission-bar-fill"
          style={{ width: `${Math.min(100, mission.progressPct)}%` }}
        />
      </div>
      <dl className="fso-mission-grid">
        <div>
          <dt>Current</dt>
          <dd>{formatKrw(mission.currentValue)}</dd>
        </div>
        <div>
          <dt>Target</dt>
          <dd>{formatKrw(mission.targetValue)}</dd>
        </div>
      </dl>
    </Panel>
  );
}
