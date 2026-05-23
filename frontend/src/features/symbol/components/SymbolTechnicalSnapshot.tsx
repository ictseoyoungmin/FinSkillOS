import { Badge, Metric, Panel } from "@/shared/ui";
import { toNumber, type Numeric } from "@/shared/lib/format";
import type { IndicatorSnapshot } from "@/features/market/kernel-types";
import type { SymbolLabHeader } from "../types";

export interface SymbolTechnicalSnapshotProps {
  header: SymbolLabHeader;
  indicators: IndicatorSnapshot;
}

function fmt(value: Numeric | null, fraction = 2): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  return Number.isFinite(n) ? n.toFixed(fraction) : "—";
}

const STATUS_TONE: Record<SymbolLabHeader["dataStatus"], "info" | "warning" | "danger"> = {
  OK: "info",
  PARTIAL: "warning",
  MISSING: "danger",
};

export function SymbolTechnicalSnapshot({
  header,
  indicators,
}: SymbolTechnicalSnapshotProps) {
  return (
    <Panel
      title="Technical Snapshot"
      badge={indicators.trendState ?? "—"}
      badgeTone="info"
      testId="technical-snapshot"
    >
      <div className="fso-kernel-chart-header">
        <div>
          <strong>{header.ticker}</strong>
          <span className="fso-kernel-chart-label">
            {header.latestTime ? header.latestTime.slice(0, 10) : "—"}
          </span>
        </div>
        <div className="fso-kernel-chart-meta">
          <span className="fso-kernel-chart-meta-num">
            {header.latestClose === null
              ? "—"
              : toNumber(header.latestClose).toFixed(2)}
          </span>
          <Badge tone={STATUS_TONE[header.dataStatus]}>{header.dataStatus}</Badge>
        </div>
      </div>
      <div className="fso-indicator-grid fso-indicator-grid--wide">
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
