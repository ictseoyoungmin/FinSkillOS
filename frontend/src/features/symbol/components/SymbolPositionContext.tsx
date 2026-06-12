import { Badge, Metric, Panel } from "@/shared/ui";
import { formatKrw, formatPct, toNumber, type Numeric } from "@/shared/lib/format";
import type { SymbolPosition } from "../types";
import "./symbol-position-context.css";

export interface SymbolPositionContextProps {
  position: SymbolPosition | null;
  ticker: string;
}

function pctOrDash(value: Numeric | null, fraction = 2): string {
  if (value === null || value === undefined) return "—";
  return `${toNumber(value).toFixed(fraction)}%`;
}

export function SymbolPositionContext({
  position,
  ticker,
}: SymbolPositionContextProps) {
  if (!position) {
    return (
      <Panel
        title="Position Context"
        badge={ticker}
        badgeTone="neutral"
        testId="position-context"
      >
        <div className="fso-symbol-context-compact">
          <strong>No current holding</strong>
          <span>{ticker} has no stored position row.</span>
        </div>
      </Panel>
    );
  }

  const weight =
    position.portfolioWeight === null
      ? "—"
      : `${(toNumber(position.portfolioWeight) * 100).toFixed(1)}%`;

  return (
    <Panel
      title="Position Context"
      badge={position.ticker}
      badgeTone={position.overSinglePositionLimit ? "warning" : "info"}
      testId="position-context"
    >
      <div className="fso-symbol-position-meta">
        {position.sector ? <Badge tone="info">{position.sector}</Badge> : null}
        {position.theme ? <Badge tone="purple">{position.theme}</Badge> : null}
        {position.strategyType ? (
          <Badge tone="neutral">{position.strategyType}</Badge>
        ) : null}
        {position.overSinglePositionLimit ? (
          <Badge tone="warning">Over Single-Position Limit</Badge>
        ) : null}
      </div>
      <div className="fso-symbol-position-grid">
        <Metric label="Market Value" value={formatKrw(position.marketValue)} />
        <Metric label="Portfolio Weight" value={weight} />
        <Metric label="Open P&L" value={pctOrDash(position.pnlPct, 2)} />
        <Metric
          label="Quantity"
          value={
            position.quantity === null
              ? "—"
              : Math.round(toNumber(position.quantity)).toLocaleString()
          }
        />
      </div>
      {position.thesis ? (
        <div className="fso-symbol-position-thesis">
          <span className="fso-symbol-position-thesis-head">Thesis</span>
          <p>{position.thesis}</p>
        </div>
      ) : null}
      <small className="fso-symbol-position-caption">
        Position view is read-only · {formatPct(position.pnlPct, 1)} P&amp;L
      </small>
    </Panel>
  );
}
