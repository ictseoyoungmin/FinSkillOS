import { Panel } from "@/shared/ui";
import type { NewsImpactMapEntry } from "../types";
import "./news-impact-map.css";

export interface NewsImpactMapProps {
  entries: NewsImpactMapEntry[];
}

/**
 * Aggregated impact map — one row per (ticker / theme / sector)
 * dimension grouping with article count + sentiment / risk pills. Lets
 * the user see where today's news cluster concentrates without
 * scrolling through every article.
 */
export function NewsImpactMap({ entries }: NewsImpactMapProps) {
  if (entries.length === 0) {
    return (
      <Panel
        title="News Impact Map"
        badge="Empty"
        badgeTone="info"
        testId="news-impact-map"
      >
        <p className="fso-news-impact-empty">
          No stored impacts available to aggregate.
        </p>
      </Panel>
    );
  }
  return (
    <Panel
      title="News Impact Map"
      badge={`${entries.length}`}
      badgeTone="info"
      testId="news-impact-map"
    >
      <table className="fso-news-impact-table" data-testid="news-impact-map-table">
        <thead>
          <tr>
            <th scope="col">Label</th>
            <th scope="col">Dimension</th>
            <th scope="col">Articles</th>
            <th scope="col">Sentiment</th>
            <th scope="col">Risk</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={`${entry.dimension}-${entry.label}`}>
              <td>{entry.label}</td>
              <td className="fso-news-impact-dim">{entry.dimension}</td>
              <td className="fso-news-impact-count">{entry.articleCount}</td>
              <td>{entry.sentiment}</td>
              <td>{entry.riskLevel}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
