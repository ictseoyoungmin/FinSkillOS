import { Panel } from "@/shared/ui";
import type { EventLinkedNewsVM } from "../types";
import "./event-linked-news-panel.css";

export interface EventLinkedNewsPanelProps {
  articles: EventLinkedNewsVM[];
}

/**
 * News rows joined via event_key / ticker to the surrounding events.
 * Mirrors the Streamlit Slice-11 page join, in compact form.
 */
export function EventLinkedNewsPanel({ articles }: EventLinkedNewsPanelProps) {
  if (articles.length === 0) {
    return (
      <Panel
        title="Linked News"
        badge="0"
        badgeTone="info"
        testId="event-linked-news"
      >
        <p className="fso-event-linked-empty">No linked news stored.</p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Linked News"
      badge={String(articles.length)}
      badgeTone="info"
      testId="event-linked-news"
    >
      <ul className="fso-event-linked-list">
        {articles.map((article) => (
          <li className="fso-event-linked-row" key={`${article.url}`}>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="fso-event-linked-title"
            >
              {article.title}
            </a>
            <div className="fso-event-linked-meta">
              {article.source} · {article.publishedAt.slice(0, 10)} ·{" "}
              {article.sentimentLabel} · {article.riskLevel}
            </div>
            <p className="fso-event-linked-summary">{article.summary}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
