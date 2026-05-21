import { Panel } from "@/shared/ui";
import type { MilestoneItem, MilestoneState } from "../types";
import "./milestone-timeline.css";

export interface MilestoneTimelineProps {
  milestones: MilestoneItem[];
}

const STATE_LABEL: Record<MilestoneState, string> = {
  COMPLETED: "Completed",
  APPROACHING: "Approaching",
  PENDING: "Pending",
};

const STATE_TONE: Record<MilestoneState, string> = {
  COMPLETED: "var(--fso-green)",
  APPROACHING: "var(--fso-amber)",
  PENDING: "var(--fso-text-muted-2)",
};

/**
 * Mission Control "Milestones" timeline (25 / 50 / 75 / 100%).
 * Pure presentational — backend decides the state.
 */
export function MilestoneTimeline({ milestones }: MilestoneTimelineProps) {
  return (
    <Panel
      title="Milestones"
      badge="Quarter Steps"
      badgeTone="info"
      testId="mission-milestone-timeline"
    >
      <ol className="fso-milestone-list">
        {milestones.map((milestone) => {
          const tone = STATE_TONE[milestone.state];
          return (
            <li
              className="fso-milestone-row"
              key={milestone.pct}
              data-state={milestone.state}
            >
              <span
                className="fso-milestone-dot"
                style={{ background: tone, borderColor: tone }}
                aria-hidden
              />
              <div className="fso-milestone-body">
                <div className="fso-milestone-pct">{milestone.pct}%</div>
                <div className="fso-milestone-label">{milestone.label}</div>
              </div>
              <span
                className="fso-milestone-state"
                style={{ color: tone, borderColor: tone }}
              >
                {STATE_LABEL[milestone.state]}
              </span>
            </li>
          );
        })}
      </ol>
    </Panel>
  );
}
