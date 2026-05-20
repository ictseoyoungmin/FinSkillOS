import { Panel } from "@/shared/ui";
import { formatPct } from "@/shared/lib/format";
import type { PortfolioExposureSlice } from "../types";
import "./portfolio-exposure-card.css";

export interface PortfolioExposureCardProps {
  slices: PortfolioExposureSlice[];
}

export function PortfolioExposureCard({ slices }: PortfolioExposureCardProps) {
  return (
    <Panel
      title="Portfolio Exposure"
      badge="Live"
      badgeTone="info"
      testId="portfolio-exposure-card"
    >
      <ul className="fso-exposure-list">
        {slices.map((slice) => (
          <li className="fso-exposure-row" key={slice.label}>
            <div className="fso-exposure-meta">
              <span className="fso-exposure-label">{slice.label}</span>
              <span className="fso-exposure-weight">
                {formatPct(slice.weightPct)}
              </span>
            </div>
            <div className="fso-exposure-bar" aria-hidden>
              <span
                style={{ width: `${Math.min(100, Number(slice.weightPct))}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
