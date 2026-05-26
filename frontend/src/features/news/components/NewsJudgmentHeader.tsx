import type { NewsJudgmentHeader as NewsJudgmentHeaderData } from "../types";
import "./news-judgment-header.css";

export interface NewsJudgmentHeaderProps {
  judgment: NewsJudgmentHeaderData;
}

export function NewsJudgmentHeader({ judgment }: NewsJudgmentHeaderProps) {
  const confidence =
    judgment.confidence === "HIGH" ? 82 : judgment.confidence === "MODERATE" ? 66 : 42;

  return (
    <section className="fso-news-judgment" data-testid="news-judgment-header">
      <div className="fso-news-judgment-copy">
        <p className="fso-news-judgment-eyebrow">Narrative Judgment</p>
        <h2>{judgment.headline}</h2>
        <div className="fso-news-judgment-tags">
          <span>{judgment.dominantTheme}</span>
          <span>{judgment.portfolioRelevance}</span>
          <span>{judgment.riskTone}</span>
        </div>
      </div>
      <div className="fso-news-judgment-confidence">
        <span>{judgment.confidence}</span>
        <strong>{confidence}%</strong>
        <i aria-hidden>
          <b style={{ width: `${confidence}%` }} />
        </i>
      </div>
    </section>
  );
}
