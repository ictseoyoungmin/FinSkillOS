import { useQuery } from "@tanstack/react-query";

import {
  fetchTossHoldingsWarnings,
  fetchTossStocks,
} from "@/features/agent/api";

import "./toss-holdings-panel.css";

/**
 * Read-only Toss enrichment for the current holdings: resolves ticker → name /
 * market / type (so bare KR codes like 052790 read as 액토즈소프트) and overlays
 * descriptive risk flags (정리매매 / 거래정지 / 투자경고 / VI). Hidden when Toss
 * isn't configured. No order controls.
 */
export function TossHoldingsPanel({ tickers }: { tickers: string[] }) {
  const symbols = [...new Set(tickers)].filter(Boolean).sort();
  const stocksQ = useQuery({
    queryKey: ["toss-stocks", symbols],
    queryFn: ({ signal }) => fetchTossStocks(symbols, signal),
    enabled: symbols.length > 0,
  });
  const warnQ = useQuery({
    queryKey: ["toss-holdings-warnings"],
    queryFn: ({ signal }) => fetchTossHoldingsWarnings(signal),
    enabled: symbols.length > 0,
  });

  const stocks = stocksQ.data;
  if (!stocks || !stocks.available) return null; // Toss not configured → hide

  const byTicker = new Map(stocks.stocks.map((s) => [s.symbol, s]));
  const warnByTicker = new Map(
    (warnQ.data?.warnings ?? []).map((w) => [w.symbol, w]),
  );

  return (
    <section className="fso-panel" data-testid="toss-holdings-panel">
      <div className="fso-panel-head">
        <span className="fso-panel-title">Holdings — names &amp; risk (Toss)</span>
      </div>
      <div className="fso-panel-body">
        <table className="fso-toss-holdings-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Name</th>
              <th>Market</th>
              <th>Risk flags</th>
            </tr>
          </thead>
          <tbody>
            {symbols.map((ticker) => {
              const s = byTicker.get(ticker);
              const w = warnByTicker.get(ticker);
              return (
                <tr key={ticker} data-testid={`toss-holding-${ticker}`}>
                  <td>{ticker}</td>
                  <td>{s?.name ?? "—"}</td>
                  <td>
                    {s?.market ?? "—"}
                    {s?.securityType === "ETF" ? " · ETF" : ""}
                  </td>
                  <td>
                    {w ? (
                      <span data-severity={w.severity}>{w.flags.join(", ")}</span>
                    ) : (
                      ""
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
