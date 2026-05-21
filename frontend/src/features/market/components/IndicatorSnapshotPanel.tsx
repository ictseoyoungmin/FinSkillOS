import { Metric, Panel } from "@/shared/ui";
import { toNumber, type Numeric } from "@/shared/lib/format";
import type { IndicatorSnapshot } from "../kernel-types";

export interface IndicatorSnapshotPanelProps {
  indicators: IndicatorSnapshot;
}

function fmt(value: Numeric | null, fraction = 2): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  return Number.isFinite(n) ? n.toFixed(fraction) : "—";
}

export function IndicatorSnapshotPanel({
  indicators,
}: IndicatorSnapshotPanelProps) {
  return (
    <Panel
      title="Indicator Snapshot"
      badge={indicators.trendState ?? "—"}
      badgeTone="info"
      testId="indicator-snapshot-panel"
    >
      <div className="fso-indicator-grid">
        <Metric label="RSI(14)" value={fmt(indicators.rsi14, 1)} />
        <Metric label="EMA(20)" value={fmt(indicators.ema20)} />
        <Metric label="EMA(60)" value={fmt(indicators.ema60)} />
        <Metric label="EMA(120)" value={fmt(indicators.ema120)} />
        <Metric label="BB Position" value={fmt(indicators.bbPosition, 3)} />
        <Metric label="Vol Z" value={fmt(indicators.volumeZScore, 2)} />
        <Metric label="Momentum" value={fmt(indicators.momentumScore, 2)} />
        <Metric label="Trend" value={indicators.trendState ?? "—"} />
      </div>
    </Panel>
  );
}
