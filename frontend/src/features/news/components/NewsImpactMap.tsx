import { Panel } from "@/shared/ui";
import type { NewsImpactMapEntry, NewsTickerIdentity } from "../types";
import { TickerLogoMark } from "./TickerLogoMark";
import "./news-impact-map.css";

export interface NewsImpactMapProps {
  entries: NewsImpactMapEntry[];
  tickerIdentities?: NewsTickerIdentity[];
}

/**
 * Aggregated impact map — one row per (ticker / theme / sector)
 * dimension grouping with article count + sentiment / risk pills. Lets
 * the user see where today's news cluster concentrates without
 * scrolling through every article.
 */
export function NewsImpactMap({
  entries,
  tickerIdentities = [],
}: NewsImpactMapProps) {
  if (entries.length === 0) {
    return (
      <Panel
        title="News Impact Map"
        badge="Empty"
        badgeTone="info"
        testId="news-impact-map"
      >
        <p className="fso-news-impact-empty" data-testid="news-impact-map-table">
          No stored impacts available to aggregate.
        </p>
      </Panel>
    );
  }

  const grouped = (["ticker", "theme", "sector"] as const)
    .map((dimension) => ({
      dimension,
      entries: entries
        .filter((entry) => entry.dimension === dimension)
        .sort((a, b) => b.articleCount - a.articleCount || a.label.localeCompare(b.label)),
    }))
    .filter((group) => group.entries.length > 0);
  const identitiesByTicker = new Map(
    tickerIdentities.map((identity) => [identity.ticker, identity]),
  );

  return (
    <Panel
      title="News Impact Map"
      badge={`${entries.length}`}
      badgeTone="info"
      testId="news-impact-map"
    >
      <div
        className="fso-news-impact-groups"
        data-testid="news-impact-map-table"
      >
        {grouped.map((group) => (
          <section className="fso-news-impact-group" key={group.dimension}>
            <h3>{group.dimension}</h3>
            <div className="fso-news-impact-chip-grid">
              {group.entries.map((entry) => (
                <div
                  className="fso-news-impact-map-chip"
                  data-risk={entry.riskLevel.toLowerCase()}
                  key={`${entry.dimension}-${entry.label}`}
                >
                  <span className="fso-news-impact-map-headline">
                    {entry.dimension === "ticker" &&
                    identitiesByTicker.has(entry.label) ? (
                      <TickerLogoMark identity={identitiesByTicker.get(entry.label)!} />
                    ) : null}
                    <span className="fso-news-impact-map-label">{entry.label}</span>
                  </span>
                  <span className="fso-news-impact-map-count">
                    {entry.articleCount}
                  </span>
                  <span className="fso-news-impact-map-meta">
                    {entry.sentiment} · {entry.riskLevel}
                  </span>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </Panel>
  );
}
