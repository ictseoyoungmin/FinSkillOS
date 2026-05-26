import { Panel } from "@/shared/ui";
import type { NewsArticleVM } from "../types";
import { PaginatedNewsList } from "./PaginatedNewsList";
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
      <PaginatedNewsList articles={articles} pageSize={5} showImpactChips />
    </Panel>
  );
}
