import type { DataSourcePill, DataSourceStatus } from "../types";
import "./data-source-strip.css";

export interface DataSourceStripProps {
  pills: DataSourcePill[];
}

const STATUS_TONE: Record<DataSourceStatus, string> = {
  LIVE: "var(--fso-green)",
  FIXTURE: "var(--fso-amber)",
  MISSING: "var(--fso-red)",
};

const STATUS_LABEL: Record<DataSourceStatus, string> = {
  LIVE: "Live",
  FIXTURE: "Fixture",
  MISSING: "Missing",
};

/**
 * Top-of-page strip of LIVE / FIXTURE / MISSING pills. Surfaces the
 * data-source status row the Slice 13.8 spec requires so the user
 * can see immediately whether the cockpit is reading live data or
 * the deterministic fixture.
 */
export function DataSourceStrip({ pills }: DataSourceStripProps) {
  return (
    <ul className="fso-data-source-strip" data-testid="system-ops-data-sources">
      {pills.map((pill) => {
        const tone = STATUS_TONE[pill.status];
        return (
          <li key={pill.label} className="fso-data-source-pill">
            <span className="fso-data-source-label">{pill.label}</span>
            <span
              className="fso-data-source-status"
              style={{ color: tone, borderColor: tone }}
            >
              {STATUS_LABEL[pill.status]}
            </span>
            <span className="fso-data-source-detail">{pill.detail}</span>
          </li>
        );
      })}
    </ul>
  );
}
