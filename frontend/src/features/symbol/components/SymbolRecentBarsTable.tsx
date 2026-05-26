import { Panel } from "@/shared/ui";
import { toNumber, type Numeric } from "@/shared/lib/format";
import type { SymbolRecentBar } from "../types";
import "./symbol-recent-bars-table.css";

export interface SymbolRecentBarsTableProps {
  bars: SymbolRecentBar[];
}

function fmt(value: Numeric | null, fraction = 2): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  return Number.isFinite(n) ? n.toFixed(fraction) : "—";
}

export function SymbolRecentBarsTable({ bars }: SymbolRecentBarsTableProps) {
  const newestFirst = [...bars].sort((a, b) => b.barTime.localeCompare(a.barTime));

  return (
    <Panel
      title="Recent Bars"
      badge={`${bars.length} rows`}
      badgeTone="info"
      testId="symbol-recent-bars"
    >
      <div className="fso-symbol-bars-scroller">
        <table className="fso-symbol-bars-table">
          <thead>
            <tr>
              <th scope="col">Time</th>
              <th scope="col">Open</th>
              <th scope="col">High</th>
              <th scope="col">Low</th>
              <th scope="col">Close</th>
              <th scope="col">Volume</th>
            </tr>
          </thead>
          <tbody>
            {newestFirst.map((bar) => (
              <tr key={bar.barTime}>
                <td>{bar.barTime.slice(0, 10)}</td>
                <td>{fmt(bar.open)}</td>
                <td>{fmt(bar.high)}</td>
                <td>{fmt(bar.low)}</td>
                <td>{fmt(bar.close)}</td>
                <td>{fmt(bar.volume, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
