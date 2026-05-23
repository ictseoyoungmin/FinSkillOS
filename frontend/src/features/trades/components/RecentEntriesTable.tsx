import { Panel } from "@/shared/ui";
import { toNumber } from "@/shared/lib/format";
import type { TradeEntryVM } from "../types";
import "./recent-entries-table.css";

export interface RecentEntriesTableProps {
  entries: TradeEntryVM[];
}

/**
 * Compact recent-entries table — date, ticker, side, regime, PnL,
 * mistake tags. Side selector vocabulary mirrors the Slice-12
 * read model (LONG / SHORT / WATCH / EXIT_REVIEW / OTHER) — legacy
 * BUY / SELL values are still load-compatible.
 */
export function RecentEntriesTable({ entries }: RecentEntriesTableProps) {
  if (entries.length === 0) {
    return (
      <Panel
        title="Recent Entries"
        badge="0"
        badgeTone="info"
        testId="recent-entries"
      >
        <p className="fso-trade-recent-empty">No journal entries yet.</p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Recent Entries"
      badge={String(entries.length)}
      badgeTone="info"
      testId="recent-entries"
    >
      <table
        className="fso-trade-recent-table"
        data-testid="trade-recent-entries-table"
      >
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Ticker</th>
            <th scope="col">Side</th>
            <th scope="col">Regime</th>
            <th scope="col">PnL</th>
            <th scope="col">R</th>
            <th scope="col">Tags</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id}>
              <td className="fso-trade-mono">{entry.tradeDate}</td>
              <td>{entry.ticker}</td>
              <td>{entry.side}</td>
              <td className="fso-trade-meta">{entry.marketRegime ?? "—"}</td>
              <td
                className={`fso-trade-pnl ${pnlClass(entry.resultPnl)}`}
              >
                {formatPnl(entry.resultPnl)}
              </td>
              <td className="fso-trade-mono">
                {entry.rMultiple !== null
                  ? Number(entry.rMultiple).toFixed(2)
                  : "—"}
              </td>
              <td>
                <ul className="fso-trade-tag-list">
                  {entry.mistakeTags.map((tag) => (
                    <li key={`${entry.id}-${tag}`}>{tag}</li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

function pnlClass(value: TradeEntryVM["resultPnl"]): string {
  if (value === null) return "";
  const n = toNumber(value);
  if (n > 0) return "fso-trade-pnl--pos";
  if (n < 0) return "fso-trade-pnl--neg";
  return "";
}

function formatPnl(value: TradeEntryVM["resultPnl"]): string {
  if (value === null) return "—";
  const n = toNumber(value);
  return n.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
