import type { TickerStripItem } from "@/features/market/types";
import "./os-ticker-strip.css";

export interface OsTickerStripProps {
  items: TickerStripItem[];
  score?: number | null;
}

const currencyMark = (currency: string): string =>
  currency === "KRW" ? "₩" : currency === "USD" ? "$" : "";

/**
 * Header ticker strip: a fixed composite-posture score pinned on the left, then a
 * horizontally sliding marquee of symbols (held first). Each item shows its native
 * currency mark and a company logo when one is resolvable. The marquee animation is
 * suppressed by `animations: "disabled"` in the Playwright config so visual
 * baselines stay stable.
 */
export function OsTickerStrip({ items, score }: OsTickerStripProps) {
  if (items.length === 0) return null;

  // Duplicate so the marquee can loop seamlessly (translateX(-50%) realigns).
  const looped = [...items, ...items];

  return (
    <div className="fso-ticker-strip" data-testid="ticker-strip">
      {score != null ? (
        <div
          className="fso-ticker-score"
          data-testid="ticker-score"
          title="Composite technical-posture score (0–100) across the strip — descriptive, not a signal"
        >
          <span className="fso-ticker-score-value">{score}</span>
          <span className="fso-ticker-score-divider" aria-hidden>
            |
          </span>
        </div>
      ) : null}
      <div className="fso-ticker-viewport">
        <div className="fso-ticker-scroll">
          {looped.map((item, idx) => (
            <span
              className={
                item.held
                  ? "fso-ticker-item fso-ticker-item--held"
                  : "fso-ticker-item"
              }
              key={`${item.symbol}-${idx}`}
            >
              {item.logoUrl ? (
                <img
                  className="fso-ticker-logo"
                  src={item.logoUrl}
                  alt=""
                  loading="lazy"
                  onError={(event) => {
                    event.currentTarget.style.display = "none";
                  }}
                />
              ) : null}
              <span className="fso-ticker-symbol">{item.symbol}</span>
              <span className="fso-ticker-price">
                {currencyMark(item.currency)}
                {item.price}
              </span>
              <span className={`fso-ticker-change fso-ticker-${item.direction}`}>
                {item.change}
              </span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
