import { Panel } from "@/shared/ui";
import type { NewsArticleVM } from "../types";
import "./news-list.css";

export interface HoldingsRelevantNewsProps {
  articles: NewsArticleVM[];
}

/**
 * Evidence panel listing news articles whose impact rows overlap one
 * of the user's current holdings. Renders the article title, source,
 * timestamp, and the short summary — never a full article body.
 */
export function HoldingsRelevantNews({ articles }: HoldingsRelevantNewsProps) {
  if (articles.length === 0) {
    return (
      <Panel
        title="Holdings-Relevant News"
        badge="0"
        badgeTone="info"
        testId="holdings-relevant-news"
      >
        <p className="fso-news-empty">
          No stored articles map to current holdings.
        </p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Holdings-Relevant News"
      badge={String(articles.length)}
      badgeTone="info"
      testId="holdings-relevant-news"
    >
      <ul className="fso-news-list">
        {articles.map((article) => (
          <li className="fso-news-row" key={article.id}>
            <div className="fso-news-row-head">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="fso-news-title"
              >
                {article.title}
              </a>
              <span className="fso-news-meta">
                {article.source} · {formatDate(article.publishedAt)}
              </span>
            </div>
            <p className="fso-news-summary">{article.summary}</p>
            {article.impacts.length > 0 ? (
              <ul className="fso-news-impact-chips">
                {article.impacts.map((impact, idx) => (
                  <li
                    className="fso-news-impact-chip"
                    key={`${article.id}-${idx}`}
                  >
                    {impact.ticker ?? impact.theme ?? impact.sector ?? "—"} ·{" "}
                    {impact.sentimentLabel}
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}
