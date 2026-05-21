import { Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { MistakeFrequencyVM } from "../types";
import "./mistake-frequency-panel.css";

export interface MistakeFrequencyPanelProps {
  rows: MistakeFrequencyVM[];
}

/** Sorted mistake-tag frequency table — count + losing-trade share + avg PnL. */
export function MistakeFrequencyPanel({ rows }: MistakeFrequencyPanelProps) {
  if (rows.length === 0) {
    return (
      <Panel
        title="Mistake Frequency"
        badge="0"
        badgeTone="info"
        testId="trade-mistake-frequency"
      >
        <p className="fso-mistake-empty">No mistake tags recorded yet.</p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Mistake Frequency"
      badge={String(rows.length)}
      badgeTone="warning"
      testId="trade-mistake-frequency"
    >
      <table
        className="fso-mistake-table"
        data-testid="trade-mistake-frequency-table"
      >
        <thead>
          <tr>
            <th scope="col">Tag</th>
            <th scope="col">Count</th>
            <th scope="col">Losing</th>
            <th scope="col">Avg PnL</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.tag}>
              <td>{row.tag}</td>
              <td className="fso-mistake-mono">{row.count}</td>
              <td className="fso-mistake-mono">{row.losingTradeCount}</td>
              <td className="fso-mistake-mono">
                {row.avgPnl !== null
                  ? toNumber(row.avgPnl).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
