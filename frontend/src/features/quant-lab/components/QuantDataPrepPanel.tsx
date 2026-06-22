import { Panel } from "@/shared/ui";
import type { QuantCoverage, QuantDataState } from "../types";

export interface QuantDataPrepPanelProps {
  coverage: QuantCoverage;
  dataState: QuantDataState;
}

const FEATURE_LABELS: Record<string, string> = {
  rsi_14: "RSI(14)",
  trend: "추세 상태",
  regime: "시장 regime",
  ema_20: "EMA(20)",
  ema_60: "EMA(60)",
};

/**
 * What data fed the backtest: the date span + bar count, and how many bars
 * actually carried each indicator/regime feature (so a sparse RSI/regime window
 * is visible rather than silently treated as "condition false").
 */
export function QuantDataPrepPanel({ coverage, dataState }: QuantDataPrepPanelProps) {
  return (
    <Panel title="Data prep" testId="quant-data-prep">
      <dl className="fso-quant-spec">
        <div>
          <dt>기간</dt>
          <dd>
            {coverage.dateStart || "—"} → {coverage.dateEnd || "—"}
          </dd>
        </div>
        <div>
          <dt>일봉 바</dt>
          <dd>{coverage.barCount}</dd>
        </div>
        <div>
          <dt>출처</dt>
          <dd>{dataState.source}</dd>
        </div>
      </dl>
      <h4 className="fso-quant-seg-head">피처 커버리지</h4>
      <div className="fso-quant-coverage" data-testid="quant-coverage">
        {coverage.features.map((f) => {
          const pct = Math.round(f.pct * 100);
          return (
            <div key={f.name} className="fso-quant-cov-row">
              <span className="fso-quant-cov-label">
                {FEATURE_LABELS[f.name] ?? f.name}
              </span>
              <span className="fso-quant-cov-bar" aria-hidden>
                <span style={{ width: `${pct}%` }} data-empty={pct === 0} />
              </span>
              <span className="fso-quant-cov-val">
                {f.bars}/{coverage.barCount} ({pct}%)
              </span>
            </div>
          );
        })}
      </div>
      <p className="fso-quant-note">{dataState.dataNote}</p>
    </Panel>
  );
}
