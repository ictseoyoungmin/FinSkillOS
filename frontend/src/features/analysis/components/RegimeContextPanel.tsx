import { Badge, EmptyState, Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { RegimeContext } from "../types";
import "./regime-context-panel.css";

export interface RegimeContextPanelProps {
  regime: RegimeContext | null;
}

export function RegimeContextPanel({ regime }: RegimeContextPanelProps) {
  if (!regime) {
    return (
      <Panel
        title="Regime Context"
        badge="No data"
        badgeTone="neutral"
        testId="regime-context"
      >
        <EmptyState
          title="No regime snapshot yet"
          message="Run the regime classifier (System Ops · Regime 재계산) to populate this card."
        />
      </Panel>
    );
  }

  const confidencePct = (toNumber(regime.confidence) * 100).toFixed(0);

  return (
    <Panel
      title="Regime Context"
      badge={regime.regime}
      badgeTone="warning"
      testId="regime-context"
    >
      <div className="fso-regime-meta">
        <Badge tone="info">{regime.decisionMode}</Badge>
        <Badge tone="warning">{`Risk · ${regime.riskLevel}`}</Badge>
        <Badge tone="neutral">{`Confidence · ${confidencePct}%`}</Badge>
      </div>
      <p className="fso-regime-summary">{regime.summary}</p>
      {regime.whatHappened ? (
        <div className="fso-regime-block">
          <span className="fso-regime-block-head">What happened</span>
          <p>{regime.whatHappened}</p>
        </div>
      ) : null}
      {regime.whatItMeans ? (
        <div className="fso-regime-block">
          <span className="fso-regime-block-head">What it means</span>
          <p>{regime.whatItMeans}</p>
        </div>
      ) : null}
      <div className="fso-regime-columns">
        {regime.positiveFactors.length > 0 ? (
          <div>
            <span className="fso-regime-col-head">Positive factors</span>
            <ul>
              {regime.positiveFactors.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {regime.riskFactors.length > 0 ? (
          <div>
            <span className="fso-regime-col-head">Risk factors</span>
            <ul>
              {regime.riskFactors.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {regime.watchNext.length > 0 ? (
          <div>
            <span className="fso-regime-col-head">Watch next</span>
            <ul>
              {regime.watchNext.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </Panel>
  );
}
