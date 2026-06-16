import { OriginTag, Panel } from "@/shared/ui";
import { formatKrw, formatPct } from "@/shared/lib/format";
import type {
  PortfolioReconciliation,
  PortfolioSnapshotPanelData,
} from "../types";
import "./portfolio-snapshot-panel.css";

export interface PortfolioSnapshotPanelProps {
  snapshot: PortfolioSnapshotPanelData;
  reconciliation?: PortfolioReconciliation;
  /** Live only: mark computed values (weight %) as DERIVED (Slice 180). */
  markDerived?: boolean;
}

/**
 * Mission Control "Portfolio Snapshot" — total / cash / position
 * count / largest position + a soft warning when any ticker exceeds
 * the configured single-position-limit threshold. Descriptive only:
 * the panel never offers a "reduce" or "exit" action.
 */
export function PortfolioSnapshotPanel({
  snapshot,
  reconciliation,
  markDerived = false,
}: PortfolioSnapshotPanelProps) {
  const overLimit = snapshot.overSingleLimitTickers;
  return (
    <Panel
      title="Portfolio Snapshot"
      badge={`${snapshot.positionCount} positions`}
      badgeTone="info"
      testId="portfolio-snapshot"
    >
      <dl className="fso-portfolio-snapshot-grid">
        {/* Total lives in the Goal Tracker (CURRENT) — don't repeat it here. */}
        <div>
          <dt>Cash</dt>
          <dd>{formatKrw(snapshot.cashValue)}</dd>
        </div>
        <div>
          <dt>Positions</dt>
          <dd>{snapshot.positionCount}</dd>
        </div>
        <div>
          <dt>Largest</dt>
          <dd>
            {snapshot.largestPositionTicker ?? "—"}
            <span className="fso-portfolio-snapshot-weight">
              {formatPct(snapshot.largestPositionWeightPct)}
            </span>
            {markDerived && snapshot.largestPositionTicker ? (
              <OriginTag origin="derived" testId="snapshot-weight-origin" />
            ) : null}
          </dd>
        </div>
      </dl>
      {overLimit.length > 0 ? (
        <p
          className="fso-portfolio-snapshot-warning"
          data-testid="mission-portfolio-snapshot-warning"
        >
          Above single-position review threshold · {overLimit.join(", ")}
        </p>
      ) : null}
      {reconciliation && reconciliation.status !== "NO_BASELINE" ? (
        <p
          className="fso-portfolio-reconciliation"
          data-status={reconciliation.status}
          data-testid="mission-portfolio-reconciliation"
        >
          {reconciliation.status === "OK"
            ? "✓ Snapshot total matches positions + cash."
            : `⚠ ${reconciliation.detail}`}
        </p>
      ) : null}
    </Panel>
  );
}
