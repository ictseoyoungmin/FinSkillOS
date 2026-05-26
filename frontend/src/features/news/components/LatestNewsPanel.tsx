import { Panel } from "@/shared/ui";
import type { NewsArticleVM } from "../types";
import { formatNewsTimestamp } from "./formatNewsTimestamp";
import "./news-list.css";

export interface LatestNewsPanelProps {
  articles: NewsArticleVM[];
}

export function LatestNewsPanel({ articles }: LatestNewsPanelProps) {
  if (articles.length === 0) {
    return (
      <Panel
        title="Latest Stored News"
        badge="0"
        badgeTone="info"
        testId="latest-stored-news"
      >
        <p className="fso-news-empty">No stored news articles yet.</p>
      </Panel>
    );
  }

  return (
    <Panel
      title="Latest Stored News"
      badge={String(articles.length)}
      badgeTone="info"
      testId="latest-stored-news"
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
                <strong>{formatNewsTimestamp(article.publishedAt)}</strong>
                <span>{article.source}</span>
              </span>
            </div>
            <p className="fso-news-summary">{article.summary}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
