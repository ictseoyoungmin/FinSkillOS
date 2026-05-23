import { Panel } from "@/shared/ui";
import { toNumber, type Numeric } from "@/shared/lib/format";
import type { IndexUniverseRow } from "../types";
import "./index-universe-table.css";

export interface IndexUniverseTableProps {
  rows: IndexUniverseRow[];
}

function fmt(value: Numeric | null, fraction = 2): string {
  if (value === null || value === undefined) return "—";
  const n = toNumber(value);
  return Number.isFinite(n) ? n.toFixed(fraction) : "—";
}

const DATA_STATUS_TONE: Record<IndexUniverseRow["dataStatus"], string> = {
  OK: "fso-status-ok",
  PARTIAL: "fso-status-partial",
  MISSING: "fso-status-missing",
};

export function IndexUniverseTable({ rows }: IndexUniverseTableProps) {
  return (
    <Panel
      title="Index Universe"
      badge={`${rows.length} rows`}
      badgeTone="info"
      testId="index-universe-table"
    >
      <div className="fso-analysis-table-scroller">
        <table className="fso-analysis-table">
          <thead>
            <tr>
              <th scope="col">Ticker</th>
              <th scope="col">Label</th>
              <th scope="col">Kind</th>
              <th scope="col">Close</th>
              <th scope="col">RSI</th>
              <th scope="col">EMA20</th>
              <th scope="col">EMA60</th>
              <th scope="col">BB Pos</th>
              <th scope="col">Vol Z</th>
              <th scope="col">Mom</th>
              <th scope="col">Trend</th>
              <th scope="col">Score</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.ticker} data-testid={`universe-row-${row.ticker}`}>
                <td>
                  <strong>{row.ticker}</strong>
                </td>
                <td>{row.label}</td>
                <td>{row.kind.replace("_", " ")}</td>
                <td>{fmt(row.latestClose)}</td>
                <td>{fmt(row.rsi14, 1)}</td>
                <td>{fmt(row.ema20)}</td>
                <td>{fmt(row.ema60)}</td>
                <td>{fmt(row.bbPosition, 3)}</td>
                <td>{fmt(row.volumeZScore, 2)}</td>
                <td>{fmt(row.momentumScore, 1)}</td>
                <td>{row.trendState ?? "—"}</td>
                <td>{fmt(row.relativeStrengthScore, 2)}</td>
                <td>
                  <span className={DATA_STATUS_TONE[row.dataStatus]}>
                    {row.dataStatus}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
