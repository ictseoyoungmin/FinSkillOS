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

  // Regime confidence is already a 0–100 score from the engine
  // (CONFIDENCE_FULL=100), matching the Control Room consumer — render as-is.
  const confidencePct = toNumber(regime.confidence).toFixed(0);
  const isStale = regime.freshness === "STALE";
  const snapshotLabel = regime.snapshotTime
    ? new Date(regime.snapshotTime).toLocaleString()
    : null;

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
        {isStale ? (
          <Badge tone="warning" testId="regime-stale">
            Stale · newer bars exist
          </Badge>
        ) : null}
      </div>
      {snapshotLabel ? (
        <p
          className="fso-regime-snapshot"
          data-stale={isStale ? "true" : "false"}
          data-testid="regime-snapshot-time"
        >
          {isStale
            ? `Computed ${snapshotLabel} — run a refresh to recompute against the latest bars.`
            : `Computed ${snapshotLabel}.`}
        </p>
      ) : null}
      <p className="fso-regime-summary">{regime.summary}</p>
      {regime.classificationRuleId ? (
        <p
          className="fso-regime-rule"
          data-testid="regime-classification-rule"
        >
          {`Classified by rule ${regime.classificationRuleId} (Skill Catalog · descriptive).`}
        </p>
      ) : null}
      {regime.confidenceRationale ? (
        <p
          className="fso-regime-confidence-rationale"
          data-testid="regime-confidence-rationale"
        >
          {regime.confidenceRationale}
        </p>
      ) : null}
      <details className="fso-regime-details">
        <summary>Context details</summary>
        {regime.attribution && regime.attribution.length > 0 ? (
          <div className="fso-regime-block">
            <span className="fso-regime-block-head">
              Indicator evidence
            </span>
            <dl
              className="fso-regime-attribution"
              data-testid="regime-attribution"
            >
              {regime.attribution.map((row) => (
                <div key={row.label}>
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}
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
      </details>
    </Panel>
  );
}
