import { useQuery } from "@tanstack/react-query";

import {
  fetchTradePerformance,
  fetchTradeStats,
  fetchTradeWeekday,
} from "@/features/trades/api";
import { formatMoney } from "@/shared/lib/format";

import "./trade-analytics-panel.css";

const pct = (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);

/**
 * Descriptive trade analytics over the journal: account-wide stats, per-ticker
 * performance, and weekday breakdown — all FIFO realized. Realized amounts are kept
 * in each trade's native currency (USD / KRW are broken out separately, never
 * mixed); ratios are currency-invariant. Hidden when there are no closed trades.
 * No buy/sell controls.
 */
export function TradeAnalyticsPanel() {
  const stats = useQuery({ queryKey: ["trade-stats"], queryFn: ({ signal }) => fetchTradeStats(signal) });
  const perf = useQuery({ queryKey: ["trade-perf"], queryFn: ({ signal }) => fetchTradePerformance(12, signal) });
  const week = useQuery({ queryKey: ["trade-weekday"], queryFn: ({ signal }) => fetchTradeWeekday(signal) });

  const s = stats.data;
  if (!s || !s.available || !s.closedCount) return null;

  const slowerLosses =
    s.avgWinHoldingDays != null &&
    s.avgLossHoldingDays != null &&
    s.avgLossHoldingDays > s.avgWinHoldingDays * 1.5;

  const currencies = Object.entries(s.byCurrency ?? {});

  return (
    <section className="fso-panel" data-testid="trade-analytics-panel">
      <div className="fso-panel-head">
        <span className="fso-panel-title">Trade Analytics (FIFO, descriptive)</span>
      </div>
      <div className="fso-panel-body">
        <div className="fso-ta-stats" data-testid="trade-analytics-stats">
          <Stat label="Closed" value={`${s.closedCount}`} sub={`${s.tickers} tickers`} />
          <Stat label="Win rate" value={pct(s.winRate)} sub={`${s.wins}W / ${s.losses}L`} />
          <Stat
            label="Hold (win / loss)"
            value={`${s.avgWinHoldingDays ?? "—"} / ${s.avgLossHoldingDays ?? "—"}d`}
            tone={slowerLosses ? "down" : undefined}
          />
          <Stat label="Avg holding" value={`${s.avgHoldingDays ?? "—"}d`} />
        </div>
        {slowerLosses ? (
          <p className="fso-ta-note" data-testid="trade-analytics-insight">
            ⚠ Losing trades are held {(s.avgLossHoldingDays! / s.avgWinHoldingDays!).toFixed(1)}×
            longer than winners — a possible cut-losses-late pattern.
          </p>
        ) : null}

        {currencies.map(([cur, c]) => (
          <div className="fso-ta-cur" key={cur} data-testid={`trade-analytics-cur-${cur}`}>
            <h4>{cur} realized (exact)</h4>
            <div className="fso-ta-stats">
              <Stat
                label="Realized"
                value={formatMoney(c.realizedPnl, cur)}
                tone={Number(c.realizedPnl) >= 0 ? "up" : "down"}
                sub={`${c.closedCount} closed`}
              />
              <Stat label="Profit factor" value={c.profitFactor ?? "—"} />
              <Stat label="Expectancy" value={formatMoney(c.expectancy, cur)} sub="per trade" />
              <Stat label="Avg win" value={formatMoney(c.avgWin, cur)} tone="up" />
              <Stat label="Avg loss" value={formatMoney(c.avgLoss, cur)} tone="down" />
              <Stat
                label="Best / worst"
                value={`${formatMoney(c.bestTrade, cur)} / ${formatMoney(c.worstTrade, cur)}`}
              />
            </div>
          </div>
        ))}

        <div className="fso-ta-cols">
          <div>
            <h4>By ticker (realized)</h4>
            <table className="fso-ta-table">
              <thead>
                <tr><th>Ticker</th><th>Realized</th><th>Win</th><th>Hold</th></tr>
              </thead>
              <tbody>
                {(perf.data?.rows ?? []).slice(0, 8).map((r) => (
                  <tr key={r.ticker} data-testid={`trade-perf-${r.ticker}`}>
                    <td>{r.ticker}</td>
                    <td className={Number(r.realizedPnl) >= 0 ? "up" : "down"}>
                      {formatMoney(r.realizedPnl, r.currency)}
                    </td>
                    <td>{pct(r.winRate)}</td>
                    <td>{r.avgHoldingDays ?? "—"}d</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <h4>By weekday</h4>
            <table className="fso-ta-table">
              <thead>
                <tr><th>Day</th><th>Trades</th><th>Win</th></tr>
              </thead>
              <tbody>
                {(week.data?.rows ?? [])
                  .filter((r) => r.tradeCount > 0)
                  .map((r) => (
                    <tr key={r.weekday}>
                      <td>{r.weekday}</td>
                      <td>{r.tradeCount}</td>
                      <td>{pct(r.winRate)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}

function Stat({ label, value, sub, tone }: {
  label: string; value: string; sub?: string; tone?: "up" | "down";
}) {
  return (
    <div className="fso-ta-stat">
      <span className="fso-ta-stat-label">{label}</span>
      <strong className={tone ? `fso-ta-${tone}` : undefined}>{value}</strong>
      {sub ? <small>{sub}</small> : null}
    </div>
  );
}
