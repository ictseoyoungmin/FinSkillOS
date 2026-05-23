import { JudgmentHeader } from "@/shared/ui";
import type { EventExposureJudgment as EventExposureJudgmentData } from "../types";

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
    <JudgmentHeader
      judgment={{
        eyebrow: "EVENT EXPOSURE JUDGMENT",
        title: "Event Cluster",
        accent: "High",
        summary: `${judgment.headline} Highest-risk event: ${judgment.highestRiskEvent}; cluster status: ${judgment.clusterStatus}.`,
        confidence: judgment.confidence === "HIGH" ? 82 : judgment.confidence === "MODERATE" ? 66 : 42,
      }}
    />
  );
}
