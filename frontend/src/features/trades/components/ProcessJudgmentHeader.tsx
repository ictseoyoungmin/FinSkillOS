import { Panel } from "@/shared/ui";
import type { ProcessJudgmentHeader as ProcessJudgmentHeaderData } from "../types";
import "./process-judgment-header.css";

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
    <Panel
      title="Process Judgment"
      badge={judgment.confidence}
      badgeTone={
        judgment.confidence === "HIGH"
          ? "success"
          : judgment.confidence === "MODERATE"
            ? "info"
            : "warning"
      }
      testId="trade-judgment-header"
    >
      <p className="fso-process-judgment-headline">{judgment.headline}</p>
      <dl className="fso-process-judgment-tags">
        <div>
          <dt>Best condition</dt>
          <dd>{judgment.bestCondition}</dd>
        </div>
        <div>
          <dt>Weakest condition</dt>
          <dd>{judgment.weakestCondition}</dd>
        </div>
        <div>
          <dt>Repeated mistake</dt>
          <dd>{judgment.repeatedMistake}</dd>
        </div>
        <div>
          <dt>Review priority</dt>
          <dd>{judgment.reviewPriority}</dd>
        </div>
      </dl>
    </Panel>
  );
}
