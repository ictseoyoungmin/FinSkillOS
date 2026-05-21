import { Panel } from "@/shared/ui";
import type { EventExposureJudgment as EventExposureJudgmentData } from "../types";
import "./event-exposure-judgment.css";

export interface EventExposureJudgmentProps {
  judgment: EventExposureJudgmentData;
}

/**
 * v4.2 Evidence-to-Judgment header for Catalyst Watch / Event Radar.
 * Surfaces the Event Exposure Judgment + confidence pill + highest-
 * risk event / cluster status / portfolio-linked exposure /
 * date-confidence mix tags.
 */
export function EventExposureJudgment({ judgment }: EventExposureJudgmentProps) {
  return (
    <Panel
      title="Event Exposure Judgment"
      badge={judgment.confidence}
      badgeTone={
        judgment.confidence === "HIGH"
          ? "success"
          : judgment.confidence === "MODERATE"
            ? "info"
            : "warning"
      }
      testId="event-judgment-header"
    >
      <p className="fso-event-judgment-headline">{judgment.headline}</p>
      <dl className="fso-event-judgment-tags">
        <div>
          <dt>Highest-risk event</dt>
          <dd>{judgment.highestRiskEvent}</dd>
        </div>
        <div>
          <dt>Cluster status</dt>
          <dd>{judgment.clusterStatus}</dd>
        </div>
        <div>
          <dt>Portfolio-linked exposure</dt>
          <dd>{judgment.portfolioLinkedExposure}</dd>
        </div>
        <div>
          <dt>Date-confidence mix</dt>
          <dd>{judgment.dateConfidenceMix}</dd>
        </div>
      </dl>
    </Panel>
  );
}
