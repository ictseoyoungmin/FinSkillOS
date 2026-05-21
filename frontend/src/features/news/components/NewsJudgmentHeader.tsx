import { Panel } from "@/shared/ui";
import type { NewsJudgmentHeader as NewsJudgmentHeaderData } from "../types";
import "./news-judgment-header.css";

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
    <Panel
      title="Narrative Judgment"
      badge={judgment.confidence}
      badgeTone={
        judgment.confidence === "HIGH"
          ? "success"
          : judgment.confidence === "MODERATE"
            ? "info"
            : "warning"
      }
      testId="news-judgment-header"
    >
      <p className="fso-news-judgment-headline">{judgment.headline}</p>
      <dl className="fso-news-judgment-tags">
        <div>
          <dt>Dominant theme</dt>
          <dd>{judgment.dominantTheme}</dd>
        </div>
        <div>
          <dt>Portfolio relevance</dt>
          <dd>{judgment.portfolioRelevance}</dd>
        </div>
        <div>
          <dt>Event linkage</dt>
          <dd>{judgment.eventLinkage}</dd>
        </div>
        <div>
          <dt>Sentiment / risk tone</dt>
          <dd>
            {judgment.sentimentTone} · {judgment.riskTone}
          </dd>
        </div>
      </dl>
    </Panel>
  );
}
