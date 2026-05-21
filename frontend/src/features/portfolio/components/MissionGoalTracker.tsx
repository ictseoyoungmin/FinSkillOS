import { Panel } from "@/shared/ui";
import { formatKrw, formatPct, toNumber } from "@/shared/lib/format";
import type { GoalTracker } from "../types";
import "./mission-goal-tracker.css";

export interface MissionGoalTrackerProps {
  goal: GoalTracker;
}

/**
 * Mission Control hero card. Mirrors the v4.1 mockup `Goal Tracker`
 * panel: large progress number + animated bar + current / target /
 * remaining metrics. Shows the goal-mode badge so the user knows
 * whether they are in GROWTH / BALANCED / PROTECTION /
 * COMPLETION_GUARD / CHALLENGE_COMPLETE.
 */
export function MissionGoalTracker({ goal }: MissionGoalTrackerProps) {
  const progressNumeric = toNumber(goal.progressPct);
  return (
    <Panel
      title="Goal Tracker"
      badge={goal.phase}
      badgeTone="info"
      testId="mission-goal-tracker"
    >
      <div className="fso-goal-tracker-figure">
        <span className="fso-goal-tracker-percent">
          {formatPct(goal.progressPct)}
        </span>
        <span className="fso-goal-tracker-mode" data-testid="mission-goal-mode">
          {goal.goalMode}
        </span>
      </div>
      <div className="fso-goal-tracker-bar" aria-hidden>
        <span
          className="fso-goal-tracker-bar-fill"
          style={{ width: `${Math.min(100, progressNumeric)}%` }}
        />
      </div>
      <dl className="fso-goal-tracker-grid">
        <div>
          <dt>Current</dt>
          <dd>{formatKrw(goal.currentValue)}</dd>
        </div>
        <div>
          <dt>Target</dt>
          <dd>{formatKrw(goal.targetValue)}</dd>
        </div>
        <div>
          <dt>Remaining</dt>
          <dd>{formatKrw(goal.remainingValue)}</dd>
        </div>
      </dl>
      <p
        className="fso-goal-tracker-challenge"
        data-testid="mission-challenge-label"
      >
        {goal.challengeLabel}
        {goal.earlyStopTriggered ? " · Challenge complete · early-stop" : null}
      </p>
    </Panel>
  );
}
