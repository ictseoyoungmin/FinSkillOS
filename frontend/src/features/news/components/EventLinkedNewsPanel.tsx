import { Panel } from "@/shared/ui";
import type { NewsArticleVM } from "../types";
import "./news-list.css";

export interface EventLinkedNewsPanelProps {
  articles: NewsArticleVM[];
}

/**
 * Evidence panel listing news articles whose impacts cite an event_key
 * — the same join the Streamlit page surfaces. Short summary only.
 */
export function EventLinkedNewsPanel({ articles }: EventLinkedNewsPanelProps) {
  if (articles.length === 0) {
    return (
      <Panel
        title="Event-Linked News"
        badge="0"
        badgeTone="info"
        testId="news-event-linked"
      >
        <p className="fso-news-empty">
          No stored articles cite an event_key.
        </p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Event-Linked News"
      badge={String(articles.length)}
      badgeTone="warning"
      testId="news-event-linked"
    >
      <ul className="fso-news-list">
        {articles.map((article) => {
          const eventKeys = article.impacts
            .map((impact) => impact.eventKey)
            .filter((key): key is string => Boolean(key));
          return (
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
                  {article.source} · {article.publishedAt.slice(0, 10)}
                  {eventKeys.length > 0
                    ? ` · ${Array.from(new Set(eventKeys)).join(", ")}`
                    : ""}
                </span>
              </div>
              <p className="fso-news-summary">{article.summary}</p>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
