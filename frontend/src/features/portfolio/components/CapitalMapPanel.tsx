import { Panel } from "@/shared/ui";
import { formatPct, toNumber } from "@/shared/lib/format";
import type { CapitalMapSlice, CapitalMapTone } from "../types";
import "./capital-map-panel.css";

export interface CapitalMapPanelProps {
  title: string;
  badge?: string;
  slices: CapitalMapSlice[];
  testId?: string;
}

const TONE_COLOR: Record<CapitalMapTone, string> = {
  info: "var(--fso-cyan)",
  warning: "var(--fso-amber)",
  danger: "var(--fso-red)",
  neutral: "var(--fso-text-muted-2)",
  success: "var(--fso-green)",
};

/**
 * Mission Control "Capital Map" — sector / theme exposure bars.
 * Drives both the sector and theme panels from a single component
 * so the page composition stays simple.
 */
export function CapitalMapPanel({
  title,
  badge,
  slices,
  testId,
}: CapitalMapPanelProps) {
  return (
    <Panel
      title={title}
      badge={badge ?? "Exposure"}
      badgeTone="info"
      testId={testId ?? "capital-map"}
    >
      {slices.length > 0 ? (
        <ul className="fso-capital-map-list">
          {slices.map((slice) => {
            const tone = TONE_COLOR[slice.tone];
            return (
              <li className="fso-capital-map-row" key={slice.label}>
                <div className="fso-capital-map-meta">
                  <span className="fso-capital-map-label">{slice.label}</span>
                  <span
                    className="fso-capital-map-weight"
                    style={{ color: tone }}
                  >
                    {formatPct(slice.weightPct)}
                  </span>
                </div>
                <div className="fso-capital-map-bar" aria-hidden>
                  <span
                    style={{
                      width: `${Math.min(100, toNumber(slice.weightPct))}%`,
                      background: tone,
                    }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="fso-capital-map-empty">
          Stored exposure rows are unavailable for this account snapshot.
        </div>
      )}
    </Panel>
  );
}
