import { Panel } from "@/shared/ui";
import type {
  NewsConflict,
  NewsDriver,
  NewsJudgmentHeader,
} from "../types";
import "./news-signal-summary.css";

export interface NewsSignalSummaryProps {
  judgment: NewsJudgmentHeader;
  drivers: NewsDriver[];
  conflicts: NewsConflict[];
}

export function NewsSignalSummary({
  judgment,
  drivers,
  conflicts,
}: NewsSignalSummaryProps) {
  const keyDrivers = drivers.slice(0, 3);
  const primaryConflict = conflicts[0];

  return (
    <Panel
      title="Feed Status"
      badge={judgment.confidence}
      badgeTone={judgment.confidence === "HIGH" ? "success" : "warning"}
      testId="news-feed-status"
    >
      <dl className="fso-news-signal-list">
        {keyDrivers.map((driver) => (
          <div className="fso-news-signal-row" key={driver.label}>
            <dt>{driver.label}</dt>
            <dd>{driver.value}</dd>
          </div>
        ))}
      </dl>
      {primaryConflict ? (
        <div className="fso-news-signal-note">
          <strong>{primaryConflict.label}</strong>
          <span>{primaryConflict.description}</span>
        </div>
      ) : null}
    </Panel>
  );
}
