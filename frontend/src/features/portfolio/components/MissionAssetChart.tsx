import { useMemo, useState } from "react";

import { LineChart } from "@/shared/charts/LineChart";
import { formatKrw, toNumber } from "@/shared/lib/format";
import { Panel } from "@/shared/ui";
import type { TimeseriesPoint } from "@/features/portfolio/types";

import "./mission-asset-chart.css";

type Metric = "asset" | "realized";
type Period = "D" | "W" | "M";

export interface MissionAssetChartProps {
  equitySeries?: TimeseriesPoint[];
  realizedSeries?: TimeseriesPoint[];
}

const METRICS: { key: Metric; label: string }[] = [
  { key: "asset", label: "자산 평가액" },
  { key: "realized", label: "실현손익 누적" },
];
const PERIODS: { key: Period; label: string }[] = [
  { key: "D", label: "일" },
  { key: "W", label: "주" },
  { key: "M", label: "월" },
];

function bucketKey(iso: string, period: Period): string {
  if (period === "D") return iso;
  const [y, m, d] = iso.split("-").map(Number);
  if (period === "M") return `${y}-${String(m).padStart(2, "0")}`;
  // Weekly → the ISO week's Monday.
  const date = new Date(Date.UTC(y, m - 1, d));
  const offset = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - offset);
  return date.toISOString().slice(0, 10);
}

// Cumulative series → keep the last point in each bucket (Map preserves the first
// insertion order, so the result stays chronological).
function aggregate(series: TimeseriesPoint[], period: Period): TimeseriesPoint[] {
  const byBucket = new Map<string, TimeseriesPoint>();
  for (const point of series) byBucket.set(bucketKey(point.date, period), point);
  return [...byBucket.values()];
}

export function MissionAssetChart({
  equitySeries = [],
  realizedSeries = [],
}: MissionAssetChartProps) {
  // Default to whichever series actually has a curve to show.
  const [metric, setMetric] = useState<Metric>(
    equitySeries.length >= 3 ? "asset" : "realized",
  );
  const [period, setPeriod] = useState<Period>("W");

  const source = metric === "asset" ? equitySeries : realizedSeries;
  const points = useMemo(() => aggregate(source, period), [source, period]);

  if (equitySeries.length === 0 && realizedSeries.length === 0) return null;

  const labels = points.map((p) => p.date.slice(5));
  const values = points.map((p) => toNumber(p.value));

  // Change vs the previous stored day (the daily series, before period bucketing).
  const prevPoint = source.length >= 2 ? source[source.length - 2] : null;
  const lastPoint = source.length >= 1 ? source[source.length - 1] : null;
  const delta =
    prevPoint && lastPoint
      ? toNumber(lastPoint.value) - toNumber(prevPoint.value)
      : null;
  const prevValue = prevPoint ? toNumber(prevPoint.value) : 0;
  const deltaPct =
    delta !== null && prevValue !== 0 ? (delta / Math.abs(prevValue)) * 100 : null;
  const deltaTone = delta === null || delta === 0 ? "flat" : delta > 0 ? "up" : "down";

  return (
    <Panel
      title="자산 변화"
      badge={metric === "asset" ? "ASSET" : "REALIZED"}
      badgeTone="info"
      testId="mission-asset-chart"
    >
      <div className="fso-asset-chart-toolbar">
        <div className="fso-asset-chart-seg" role="tablist" aria-label="Metric">
          {METRICS.map((m) => (
            <button
              key={m.key}
              type="button"
              className={m.key === metric ? "fso-asset-seg-btn is-active" : "fso-asset-seg-btn"}
              onClick={() => setMetric(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>
        <div className="fso-asset-chart-seg" role="tablist" aria-label="Period">
          {PERIODS.map((p) => (
            <button
              key={p.key}
              type="button"
              className={p.key === period ? "fso-asset-seg-btn is-active" : "fso-asset-seg-btn"}
              onClick={() => setPeriod(p.key)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      {delta !== null ? (
        <div className={`fso-asset-delta fso-asset-delta--${deltaTone}`} data-testid="mission-asset-delta">
          <strong>
            {delta >= 0 ? "+" : "−"}
            {formatKrw(Math.abs(delta))}
          </strong>
          {deltaPct !== null ? (
            <span>
              {deltaPct >= 0 ? "+" : "−"}
              {Math.abs(deltaPct).toFixed(2)}%
            </span>
          ) : null}
          <small>직전 {prevPoint?.date.slice(5)} 대비</small>
        </div>
      ) : null}
      {points.length >= 2 ? (
        <LineChart
          labels={labels}
          series={[{ name: metric, values, tone: "primary" }]}
          caption="누적 · KRW(원화 환산) · 서술용, 예측 아님"
          testId="mission-asset-line"
        />
      ) : (
        <p className="fso-asset-chart-empty" data-testid="mission-asset-empty">
          {metric === "asset"
            ? "자산 평가액 이력이 쌓이는 중입니다 — 동기화할 때마다 일별로 기록됩니다."
            : "표시할 실현손익 이력이 아직 없습니다."}
        </p>
      )}
    </Panel>
  );
}
