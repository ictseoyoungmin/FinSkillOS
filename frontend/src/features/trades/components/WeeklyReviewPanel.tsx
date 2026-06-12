import { Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { WeeklyReviewVM } from "../types";
import "./weekly-review-panel.css";

export interface WeeklyReviewNavigation {
  /** 0 = current week, 1 = one week back, … */
  weekOffset: number;
  loading: boolean;
  onPrev: () => void;
  onNext: () => void;
  onThisWeek: () => void;
}

export interface WeeklyReviewPanelProps {
  review: WeeklyReviewVM;
  /** Live-only week stepper; omitted (fixture/offline) renders the static card. */
  navigation?: WeeklyReviewNavigation;
}

/**
 * Weekly review summary card. Reads the 7-day window the
 * ReflectionService computes and surfaces trade count, total PnL,
 * win rate, top mistakes, best / weakest regime, and process notes.
 *
 * When ``navigation`` is supplied (live mode) the header gains a prev / next /
 * this-week stepper so completed weeks can be reviewed (Slice 161).
 */
export function WeeklyReviewPanel({ review, navigation }: WeeklyReviewPanelProps) {
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
      {navigation ? (
        <div
          className="fso-weekly-review-nav"
          data-testid="weekly-review-nav"
        >
          <button
            type="button"
            onClick={navigation.onPrev}
            disabled={navigation.loading}
            data-testid="weekly-review-prev"
            aria-label="Previous week"
          >
            ◀ Prev
          </button>
          <span data-testid="weekly-review-window-label">
            {navigation.weekOffset === 0
              ? "This week"
              : `${navigation.weekOffset} week${
                  navigation.weekOffset === 1 ? "" : "s"
                } ago`}
            {navigation.loading ? " · loading…" : ""}
          </span>
          <button
            type="button"
            onClick={navigation.onNext}
            disabled={navigation.loading || navigation.weekOffset === 0}
            data-testid="weekly-review-next"
            aria-label="Next week"
          >
            Next ▶
          </button>
          {navigation.weekOffset !== 0 ? (
            <button
              type="button"
              className="fso-weekly-review-thisweek"
              onClick={navigation.onThisWeek}
              disabled={navigation.loading}
              data-testid="weekly-review-thisweek"
            >
              This week
            </button>
          ) : null}
        </div>
      ) : null}
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
  // P&L amounts display as whole units (decimals add noise without meaning).
  return Math.round(toNumber(value)).toLocaleString("en-US");
}
