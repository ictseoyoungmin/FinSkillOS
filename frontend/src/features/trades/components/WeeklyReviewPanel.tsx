import { Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { WeeklyReviewVM } from "../types";
import "./weekly-review-panel.css";

export interface WeeklyReviewPanelProps {
  review: WeeklyReviewVM;
}

/**
 * Weekly review summary card. Reads the 7-day window the
 * ReflectionService computes and surfaces trade count, total PnL,
 * win rate, top mistakes, best / weakest regime, and process notes.
 */
export function WeeklyReviewPanel({ review }: WeeklyReviewPanelProps) {
  const winRate =
    review.winRate === null
      ? "—"
      : `${(toNumber(review.winRate) * 100).toFixed(1)}%`;
  return (
    <Panel
      title="Weekly Review"
      badge={`${review.startDate} → ${review.endDate}`}
      badgeTone="info"
      testId="weekly-review"
    >
      <dl className="fso-weekly-review-stats">
        <div>
          <dt>Trades</dt>
          <dd>{review.tradeCount}</dd>
        </div>
        <div>
          <dt>Total P&amp;L</dt>
          <dd>{formatNumber(review.totalPnl)}</dd>
        </div>
        <div>
          <dt>Win rate</dt>
          <dd>{winRate}</dd>
        </div>
      </dl>
      {review.mostCommonMistakes.length > 0 ? (
        <div className="fso-weekly-review-block">
          <h3>Most common mistakes</h3>
          <ul>
            {review.mostCommonMistakes.map((mistake) => (
              <li key={mistake.tag}>
                <span className="fso-weekly-review-tag">{mistake.tag}</span> —{" "}
                {mistake.count} entries · {mistake.losingTradeCount} losing
                {mistake.avgPnl !== null
                  ? ` · avg ${formatNumber(mistake.avgPnl)}`
                  : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {review.bestRegime ? (
        <p className="fso-weekly-review-line">
          <strong>Best regime:</strong> {review.bestRegime.key} (total{" "}
          {formatNumber(review.bestRegime.totalPnl)})
        </p>
      ) : null}
      {review.weakestRegime &&
      review.weakestRegime.key !== review.bestRegime?.key ? (
        <p className="fso-weekly-review-line">
          <strong>Weakest regime:</strong> {review.weakestRegime.key} (total{" "}
          {formatNumber(review.weakestRegime.totalPnl)})
        </p>
      ) : null}
      {review.processNotes.length > 0 ? (
        <ul className="fso-weekly-review-notes">
          {review.processNotes.map((note, index) => (
            <li key={index}>{note}</li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}

function formatNumber(value: WeeklyReviewVM["totalPnl"]): string {
  return toNumber(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
