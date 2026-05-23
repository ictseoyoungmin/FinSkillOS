import { JudgmentHeader } from "@/shared/ui";
import type { ProcessJudgmentHeader as ProcessJudgmentHeaderData } from "../types";

export interface ProcessJudgmentHeaderProps {
  judgment: ProcessJudgmentHeaderData;
}

/**
 * v4.2 Evidence-to-Judgment header for Trade Memory. Surfaces the
 * Process Judgment headline + confidence pill plus the best /
 * weakest condition / repeated mistake / review priority tags.
 */
export function ProcessJudgmentHeader({
  judgment,
}: ProcessJudgmentHeaderProps) {
  return (
    <div data-testid="trade-judgment-header">
      <JudgmentHeader
        judgment={{
          eyebrow: "PROCESS JUDGMENT",
          title: "Profits in Risk-On,",
          accent: "Losses in FOMO",
          summary: `${judgment.headline} Best condition: ${judgment.bestCondition}; review priority: ${judgment.reviewPriority}.`,
          confidence: judgment.confidence === "HIGH" ? 82 : judgment.confidence === "MODERATE" ? 66 : 42,
        }}
      />
    </div>
  );
}
