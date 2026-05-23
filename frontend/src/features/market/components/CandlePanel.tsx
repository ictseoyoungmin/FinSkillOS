import { Badge, Panel } from "@/shared/ui";
import { LineChart } from "@/shared/charts/LineChart";
import { toNumber } from "@/shared/lib/format";
import type { MarketBarPoint, MarketKernelHeader } from "../kernel-types";

export interface CandlePanelProps {
  header: MarketKernelHeader;
  bars: MarketBarPoint[];
  /** Optional badge text shown next to the panel title. */
  badge?: string;
}

function shortenBarTime(iso: string): string {
  if (!iso) return "";
  const [date] = iso.split("T");
  return date?.slice(5) ?? iso;
}

/**
 * Stored-bar line chart for the Market Kernel page.
 *
 * Slice 13.7 deliberately keeps this descriptive: close-line + EMA
 * overlays only when present. No drawing tools, no overlays beyond
 * what the indicator snapshot already publishes. The "Stored data
 * only" caption is non-removable.
 */
export function CandlePanel({ header, bars, badge }: CandlePanelProps) {
  const labels = bars.map((bar) => shortenBarTime(bar.barTime));
  const closes = bars.map((bar) => bar.close);
  const dataStatusTone =
    header.dataStatus === "OK"
      ? "info"
      : header.dataStatus === "PARTIAL"
        ? "warning"
        : "danger";

  return (
    <Panel
      title={`Chart · ${header.ticker}`}
      badge={badge ?? header.timeframe.toUpperCase()}
      badgeTone="info"
      testId="chart-panel"
    >
      <div className="fso-kernel-chart-header" data-testid="market-kernel-header">
        <div>
          <strong>{header.ticker}</strong>
          <span className="fso-kernel-chart-label">{header.label}</span>
        </div>
        <div className="fso-kernel-chart-meta">
          <span className="fso-kernel-chart-meta-num">
            {header.latestClose === null ? "—" : toNumber(header.latestClose).toFixed(2)}
          </span>
          <Badge tone={dataStatusTone}>{header.dataStatus}</Badge>
        </div>
      </div>
      <LineChart
        labels={labels}
        series={[{ name: "close", values: closes, tone: "primary" }]}
        testId="market-kernel-line-chart"
        caption="Stored data only · not prediction · no execution"
      />
    </Panel>
  );
}
