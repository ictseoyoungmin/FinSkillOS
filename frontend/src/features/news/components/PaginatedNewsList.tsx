import { useEffect, useMemo, useState } from "react";
import type { NewsArticleVM, NewsTickerIdentity } from "../types";
import { shouldShowArticleSummary } from "./articleText";
import { formatNewsTimestamp } from "./formatNewsTimestamp";
import { TickerLogoMark } from "./TickerLogoMark";
import "./news-list.css";

const DEFAULT_PAGE_SIZE = 5;

export interface PaginatedNewsListProps {
  articles: NewsArticleVM[];
  pageSize?: number;
  showEventKeys?: boolean;
  showImpactChips?: boolean;
  tickerIdentities?: NewsTickerIdentity[];
}

export function PaginatedNewsList({
  articles,
  pageSize = DEFAULT_PAGE_SIZE,
  showEventKeys = false,
  showImpactChips = false,
  tickerIdentities = [],
}: PaginatedNewsListProps) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(articles.length / pageSize));

  useEffect(() => {
    setPage(0);
  }, [articles, pageSize]);

  const visibleArticles = useMemo(() => {
    const start = page * pageSize;
    return articles.slice(start, start + pageSize);
  }, [articles, page, pageSize]);

  const identitiesByTicker = useMemo(
    () =>
      new Map(
        tickerIdentities.map((identity) => [identity.ticker, identity]),
      ),
    [tickerIdentities],
  );

  return (
    <>
      <ul className="fso-news-list">
        {visibleArticles.map((article) => {
          const eventKeys = Array.from(
            new Set(
              article.impacts
                .map((impact) => impact.eventKey)
                .filter((key): key is string => Boolean(key)),
            ),
          );
          const logoIdentity = article.impacts
            .map((impact) =>
              impact.ticker ? identitiesByTicker.get(impact.ticker) : undefined,
            )
            .find((identity): identity is NewsTickerIdentity => Boolean(identity));

          return (
            <li className="fso-news-row" key={article.id}>
              <div className="fso-news-row-main">
                {logoIdentity ? <TickerLogoMark identity={logoIdentity} /> : null}
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
                    {showEventKeys && eventKeys.length > 0 ? (
                      <span>{eventKeys.join(", ")}</span>
                    ) : null}
                  </span>
                </div>
              </div>
              {shouldShowArticleSummary(article) ? (
                <p className="fso-news-summary">{article.summary}</p>
              ) : null}
              {showImpactChips && article.impacts.length > 0 ? (
                <ul className="fso-news-impact-chips">
                  {article.impacts.map((impact, idx) => (
                    <li
                      className="fso-news-impact-chip"
                      key={`${article.id}-${idx}`}
                    >
                      {impact.ticker ?? impact.theme ?? impact.sector ?? "-"} ·{" "}
                      {impact.sentimentLabel}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>
      {pageCount > 1 ? (
        <div className="fso-news-pagination" aria-label="News pagination">
          <button
            type="button"
            onClick={() => setPage((current) => Math.max(0, current - 1))}
            disabled={page === 0}
          >
            Prev
          </button>
          <span>
            {page + 1} / {pageCount}
          </span>
          <button
            type="button"
            onClick={() =>
              setPage((current) => Math.min(pageCount - 1, current + 1))
            }
            disabled={page >= pageCount - 1}
          >
            Next
          </button>
        </div>
      ) : null}
    </>
  );
}
