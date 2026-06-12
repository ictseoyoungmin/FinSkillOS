import { useQuery } from "@tanstack/react-query";

import {
  fetchTradePerformance,
  fetchTradeStats,
  fetchTradeWeekday,
} from "@/features/trades/api";
import { formatKrw } from "@/shared/lib/format";

import "./trade-analytics-panel.css";

const pct = (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const krw = (v: string | null) =>
  v == null ? "—" : formatKrw(Number(v));

/**
 * Descriptive trade analytics over the journal: account-wide stats, per-ticker
 * performance, and weekday breakdown — all FIFO realized. Hidden when there are no
 * closed trades. No buy/sell controls. (Absolute amounts are KRW; ratios exact.)
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

  return (
    <section className="fso-panel" data-testid="trade-analytics-panel">
      <div className="fso-panel-head">
        <span className="fso-panel-title">Trade Analytics (FIFO, descriptive)</span>
      </div>
      <div className="fso-panel-body">
        <div className="fso-ta-stats" data-testid="trade-analytics-stats">
          <Stat label="Closed" value={`${s.closedCount}`} sub={`${s.tickers} tickers`} />
          <Stat label="Win rate" value={pct(s.winRate)} sub={`${s.wins}W / ${s.losses}L`} />
          <Stat label="Profit factor" value={s.profitFactor ?? "—"} />
          <Stat label="Expectancy" value={krw(s.expectancy)} sub="per trade" />
          <Stat label="Avg win" value={krw(s.avgWin)} tone="up" />
          <Stat label="Avg loss" value={krw(s.avgLoss)} tone="down" />
          <Stat
            label="Hold (win / loss)"
            value={`${s.avgWinHoldingDays ?? "—"} / ${s.avgLossHoldingDays ?? "—"}d`}
            tone={slowerLosses ? "down" : undefined}
          />
          <Stat label="Best / worst" value={`${krw(s.bestTrade)} / ${krw(s.worstTrade)}`} />
        </div>
        {slowerLosses ? (
          <p className="fso-ta-note" data-testid="trade-analytics-insight">
            ⚠ Losing trades are held {(s.avgLossHoldingDays! / s.avgWinHoldingDays!).toFixed(1)}×
            longer than winners — a possible cut-losses-late pattern.
          </p>
        ) : null}

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
                    <td className={Number(r.realizedPnl) >= 0 ? "up" : "down"}>{krw(r.realizedPnl)}</td>
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
                <tr><th>Day</th><th>Trades</th><th>Realized</th><th>Win</th></tr>
              </thead>
              <tbody>
                {(week.data?.rows ?? [])
                  .filter((r) => r.tradeCount > 0)
                  .map((r) => (
                    <tr key={r.weekday}>
                      <td>{r.weekday}</td>
                      <td>{r.tradeCount}</td>
                      <td className={Number(r.realizedPnl) >= 0 ? "up" : "down"}>{krw(r.realizedPnl)}</td>
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
