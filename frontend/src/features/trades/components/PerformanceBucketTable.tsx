import { toNumber } from "@/shared/lib/format";
import type { PerformanceBucketVM } from "../types";
import "./performance-bucket-table.css";

export interface PerformanceBucketTableProps {
  buckets: PerformanceBucketVM[];
  keyHeader: string;
}

/** Shared performance breakdown table used by the three PerformanceBy* wrappers. */
export function PerformanceBucketTable({
  buckets,
  keyHeader,
}: PerformanceBucketTableProps) {
  if (buckets.length === 0) {
    return (
      <p className="fso-perf-empty">No performance bucket data yet.</p>
    );
  }
  return (
    <table className="fso-perf-table">
      <thead>
        <tr>
          <th scope="col">{keyHeader}</th>
          <th scope="col">Trades</th>
          <th scope="col">Total PnL</th>
          <th scope="col">Avg PnL</th>
          <th scope="col">Avg R</th>
          <th scope="col">Win rate</th>
        </tr>
      </thead>
      <tbody>
        {buckets.map((bucket) => (
          <tr key={bucket.key}>
            <td>{bucket.key}</td>
            <td className="fso-perf-mono">{bucket.tradeCount}</td>
            <td className={`fso-perf-mono ${pnlClass(bucket.totalPnl)}`}>
              {formatNum(bucket.totalPnl)}
            </td>
            <td className={`fso-perf-mono ${pnlClass(bucket.avgPnl)}`}>
              {formatNum(bucket.avgPnl)}
            </td>
            <td className="fso-perf-mono">
              {bucket.avgRMultiple !== null
                ? Number(bucket.avgRMultiple).toFixed(2)
                : "—"}
            </td>
            <td className="fso-perf-mono">
              {bucket.winRate !== null
                ? `${(toNumber(bucket.winRate) * 100).toFixed(1)}%`
                : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function formatNum(value: PerformanceBucketVM["totalPnl"]): string {
  return toNumber(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function pnlClass(value: PerformanceBucketVM["totalPnl"]): string {
  const n = toNumber(value);
  if (n > 0) return "fso-perf-pos";
  if (n < 0) return "fso-perf-neg";
  return "";
}
