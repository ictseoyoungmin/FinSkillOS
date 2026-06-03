import { useQuery } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { fetchFeedCoverage } from "../api";

/**
 * News + event feed coverage diagnostics (Slice 154): how much is stored, how
 * fresh, and from which sources — so an operator can tell whether a thin News /
 * Catalyst tab is a feed gap rather than a quiet market.
 */
export function FeedCoveragePanel(): JSX.Element {
  const { data, isError } = useQuery({
    queryKey: ["feed-coverage"],
    queryFn: ({ signal }) => fetchFeedCoverage(signal),
  });

  if (isError) {
    return (
      <Panel title="Feed Coverage" badge="unavailable" badgeTone="warning">
        <p className="fso-provenance-detail">
          Feed coverage could not be read from the database.
        </p>
      </Panel>
    );
  }

  const report = data;
  const newsTone =
    !report || report.news.freshnessStatus === "EMPTY"
      ? "neutral"
      : report.news.freshnessStatus === "FRESH"
        ? "success"
        : "warning";

  return (
    <Panel
      title="Feed Coverage"
      badge={report ? report.news.freshnessStatus.toLowerCase() : "loading"}
      badgeTone={newsTone}
    >
      <p className="fso-provenance-detail" data-testid="feed-coverage-detail">
        {report?.detail ?? "Reading news + event feed coverage…"}
      </p>
      {report ? (
        <div className="fso-feed-grid" data-testid="feed-coverage-grid">
          <div className="fso-feed-block">
            <span className="fso-feed-block-head">News</span>
            <span className="fso-feed-stat">
              {report.news.totalArticles.toLocaleString()} stored ·{" "}
              {report.news.recentArticles} in 7d
            </span>
            <div className="fso-feed-sources">
              {report.news.sources.slice(0, 5).map((s) => (
                <span key={s.source} className="fso-feed-source">
                  {s.source} ({s.count})
                </span>
              ))}
            </div>
          </div>
          <div className="fso-feed-block">
            <span className="fso-feed-block-head">Events</span>
            <span className="fso-feed-stat">
              {report.events.totalEvents.toLocaleString()} stored ·{" "}
              {report.events.upcomingEvents} upcoming
            </span>
            <div className="fso-feed-sources">
              {report.events.dateStatus.slice(0, 5).map((s) => (
                <span key={s.source} className="fso-feed-source">
                  {s.source} ({s.count})
                </span>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}
