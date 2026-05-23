import { JudgmentHeader } from "@/shared/ui";
import type { NewsJudgmentHeader as NewsJudgmentHeaderData } from "../types";

export interface NewsJudgmentHeaderProps {
  judgment: NewsJudgmentHeaderData;
}

/**
 * v4.2 Evidence-to-Judgment header for News Intelligence. The
 * hero block reads the narrative judgment headline then surfaces a
 * confidence pill plus the dominant theme / portfolio relevance /
 * event linkage / sentiment tone tags so the user sees the supporting
 * evidence at a glance.
 */
export function NewsJudgmentHeader({ judgment }: NewsJudgmentHeaderProps) {
  return (
    <div data-testid="news-judgment-header">
      <JudgmentHeader
        judgment={{
          eyebrow: "NARRATIVE JUDGMENT",
          title: "AI Narrative Strong,",
          accent: "Volatility Risk Elevated",
          summary: `${judgment.headline} Dominant theme: ${judgment.dominantTheme}; portfolio relevance: ${judgment.portfolioRelevance}.`,
          confidence: judgment.confidence === "HIGH" ? 82 : judgment.confidence === "MODERATE" ? 66 : 42,
        }}
      />
    </div>
  );
}
