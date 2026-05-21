import { Badge, EmptyState, Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { SymbolNewsItem } from "../types";
import "./symbol-news-panel.css";

export interface SymbolNewsPanelProps {
  news: SymbolNewsItem[];
}

const SENTIMENT_TONE: Record<string, "success" | "warning" | "neutral" | "danger"> = {
  POSITIVE: "success",
  NEGATIVE: "danger",
  MIXED: "warning",
  NEUTRAL: "neutral",
  UNKNOWN: "neutral",
};

export function SymbolNewsPanel({ news }: SymbolNewsPanelProps) {
  return (
    <Panel
      title="Symbol News"
      badge={`${news.length}`}
      badgeTone="info"
      testId="symbol-news-panel"
    >
      {news.length === 0 ? (
        <EmptyState
          title="No tracked news"
          message="No news impacts are linked to this ticker in the stored data."
        />
      ) : (
        <ul className="fso-symbol-news">
          {news.map((item) => (
            <li key={item.url || item.title}>
              <div className="fso-symbol-news-head">
                <a
                  href={item.url || "#"}
                  rel="noreferrer"
                  target="_blank"
                  className="fso-symbol-news-title"
                >
                  {item.title}
                </a>
                <Badge tone={SENTIMENT_TONE[item.sentimentLabel] ?? "neutral"}>
                  {item.sentimentLabel}
                </Badge>
              </div>
              <small className="fso-symbol-news-meta">
                {item.source} · {item.publishedAt.slice(0, 10)} · impact{" "}
                {toNumber(item.impactScore).toFixed(2)}
              </small>
              {item.riskNote ? (
                <p className="fso-symbol-news-risk">{item.riskNote}</p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
