import type { TickerStripItem } from "@/features/market/types";
import "./os-ticker-strip.css";

export interface OsTickerStripProps {
  items: TickerStripItem[];
}

/**
 * Horizontally scrolling ticker strip. Items are deterministic via
 * the Slice 13.6 fixture so Playwright visual baselines stay stable —
 * the CSS animation is suppressed by `animations: "disabled"` in the
 * Playwright config.
 */
export function OsTickerStrip({ items }: OsTickerStripProps) {
  if (items.length === 0) return null;

  // Duplicate so the marquee loop has enough content for the slide.
  const looped = [...items, ...items];

  return (
    <div className="fso-ticker-strip" data-testid="ticker-strip">
      <div className="fso-ticker-scroll">
        {looped.map((item, idx) => (
          <span className="fso-ticker-item" key={`${item.symbol}-${idx}`}>
            <span className="fso-ticker-symbol">{item.symbol}</span>
            <span className="fso-ticker-price">{item.price}</span>
            <span className={`fso-ticker-change fso-ticker-${item.direction}`}>
              {item.change}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
