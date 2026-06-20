import { Metric, Panel } from "@/shared/ui";
import type { QuantMetrics } from "../types";

function pct(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function ratio(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";
  return value.toFixed(2);
}

export interface QuantMetricsPanelProps {
  metrics: QuantMetrics;
}

/**
 * The absorbed METRIC rulebook stats for a simulated run — descriptive
 * observation of how the hypothesis *would have* behaved over stored bars.
 */
export function QuantMetricsPanel({ metrics }: QuantMetricsPanelProps) {
  return (
    <Panel title="Simulation metrics" testId="quant-metrics">
      <p className="fso-quant-note">저장된 과거 바 리플레이 관측치 (미래 성과 아님)</p>
      <div className="fso-quant-metrics-grid">
        <Metric label="누적 수익" value={pct(metrics.totalReturn)} testId="quant-metric-total" />
        <Metric label="CAGR" value={pct(metrics.cagr)} />
        <Metric label="연 변동성" value={pct(metrics.annualVolatility)} />
        <Metric label="Sharpe" value={ratio(metrics.sharpe)} testId="quant-metric-sharpe" />
        <Metric label="Sortino" value={ratio(metrics.sortino)} />
        <Metric label="Calmar" value={ratio(metrics.calmar)} />
        <Metric label="최대 낙폭" value={pct(metrics.maxDrawdown)} />
        <Metric label="노출 비중" value={pct(metrics.exposurePct)} testId="quant-metric-exposure" />
        <Metric label="라운드트립" value={metrics.roundTrips} />
        <Metric label="승률" value={pct(metrics.winRate)} />
      </div>
    </Panel>
  );
}
