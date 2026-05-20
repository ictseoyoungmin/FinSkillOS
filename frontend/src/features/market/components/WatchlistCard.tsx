import { Badge, Panel } from "@/shared/ui";
import type { WatchlistItem } from "../types";
import "./watchlist-card.css";

export interface WatchlistCardProps {
  items: WatchlistItem[];
}

export function WatchlistCard({ items }: WatchlistCardProps) {
  return (
    <Panel
      title="Watchlist"
      badge="Live"
      badgeTone="info"
      testId="watchlist-card"
    >
      <ul className="fso-watchlist">
        {items.map((item) => (
          <li className="fso-watchlist-row" key={item.symbol}>
            <div className="fso-watchlist-symbol">{item.symbol}</div>
            <div className="fso-watchlist-meta">
              <span className="fso-watchlist-label">{item.label}</span>
              <span className="fso-watchlist-note">{item.note}</span>
            </div>
            <Badge tone={item.tone}>{item.tone}</Badge>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
