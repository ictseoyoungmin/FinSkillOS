import { Panel } from "@/shared/ui";
import type { NewsArticleVM } from "../types";
import { PaginatedNewsList } from "./PaginatedNewsList";
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
        testId="event-linked-news"
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
      testId="event-linked-news"
    >
      <PaginatedNewsList articles={articles} pageSize={5} showEventKeys />
    </Panel>
  );
}
