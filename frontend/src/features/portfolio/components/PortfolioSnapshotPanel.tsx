import { Panel } from "@/shared/ui";
import { formatKrw, formatPct } from "@/shared/lib/format";
import type { PortfolioSnapshotPanelData } from "../types";
import "./portfolio-snapshot-panel.css";

export interface PortfolioSnapshotPanelProps {
  snapshot: PortfolioSnapshotPanelData;
}

/**
 * Mission Control "Portfolio Snapshot" — total / cash / position
 * count / largest position + a soft warning when any ticker exceeds
 * the configured single-position-limit threshold. Descriptive only:
 * the panel never offers a "reduce" or "exit" action.
 */
export function PortfolioSnapshotPanel({ snapshot }: PortfolioSnapshotPanelProps) {
  const overLimit = snapshot.overSingleLimitTickers;
  return (
    <Panel
      title="Portfolio Snapshot"
      badge={`${snapshot.positionCount} positions`}
      badgeTone="info"
      testId="mission-portfolio-snapshot"
    >
      <dl className="fso-portfolio-snapshot-grid">
        <div>
          <dt>Total</dt>
          <dd>{formatKrw(snapshot.totalValue)}</dd>
        </div>
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
    </Panel>
  );
}
