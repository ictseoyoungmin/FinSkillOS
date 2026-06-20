import { LineChart } from "@/shared/charts/LineChart";
import { Panel } from "@/shared/ui";
import type { QuantEquityPoint } from "../types";

export interface QuantEquityChartProps {
  curve: QuantEquityPoint[];
  ticker: string;
}

/**
 * Equity vs buy-and-hold benchmark, normalised to a 1.0 start. Descriptive —
 * no overlays, no forecast labels; the strategy line is simply the replayed
 * hypothesis, the benchmark is holding the same asset.
 */
export function QuantEquityChart({ curve, ticker }: QuantEquityChartProps) {
  const labels = curve.map((p) => p.date);
  const strategy = curve.map((p) => p.strategy);
  const benchmark = curve.map((p) => p.benchmark);
  const exposedDays = curve.filter((p) => p.exposure).length;

  return (
    <Panel title="Equity curve vs benchmark" testId="quant-equity-chart">
      <p className="fso-quant-note">
        전략(노출 ON 구간만 자산 수익 반영) vs {ticker} 단순 보유 · 시작값 1.0 정규화 ·
        노출 {exposedDays}/{curve.length} 바
      </p>
      {curve.length > 0 ? (
        <LineChart
          labels={labels}
          series={[
            { name: "전략", values: strategy, tone: "primary" },
            { name: `${ticker} 보유`, values: benchmark, tone: "muted", dashed: true },
          ]}
          height={280}
          valueFormat={(v) => v.toFixed(3)}
          testId="quant-equity-linechart"
          caption="정규화 누적 성장 (1.0 = 시작 자본). 관측 결과이며 미래를 뜻하지 않습니다."
        />
      ) : (
        <p className="fso-quant-empty">표시할 시뮬레이션 곡선이 없습니다.</p>
      )}
    </Panel>
  );
}
