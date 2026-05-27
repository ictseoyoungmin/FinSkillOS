import { Panel } from "@/shared/ui";
import type { NewsArticleVM, NewsTickerIdentity } from "../types";
import { PaginatedNewsList } from "./PaginatedNewsList";
import "./news-list.css";

export interface LatestNewsPanelProps {
  articles: NewsArticleVM[];
  tickerIdentities?: NewsTickerIdentity[];
}

export function LatestNewsPanel({
  articles,
  tickerIdentities = [],
}: LatestNewsPanelProps) {
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
      <PaginatedNewsList
        articles={articles}
        pageSize={4}
        tickerIdentities={tickerIdentities}
      />
    </Panel>
  );
}
