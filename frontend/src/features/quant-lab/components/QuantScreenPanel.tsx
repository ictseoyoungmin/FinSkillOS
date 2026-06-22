import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Panel } from "@/shared/ui";
import { fetchQuantLabScreen, screenQuantLabSpec } from "../api";

export interface QuantScreenPanelProps {
  strategyId: string;
  strategyName: string;
  currentTicker: string;
  customSpec: Record<string, unknown> | null;
  onPick: (ticker: string) => void;
}

function pct(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : `${(v * 100).toFixed(1)}%`;
}

function ratio(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : v.toFixed(2);
}

/**
 * Multi-asset screen: run the current strategy across every stored ticker and
 * rank by cumulative return. On-demand (the backtests are run server-side only
 * when asked). Picking a row deep-links the tab to that ticker.
 */
export function QuantScreenPanel({
  strategyId,
  strategyName,
  currentTicker,
  customSpec,
  onPick,
}: QuantScreenPanelProps) {
  const [open, setOpen] = useState(false);
  const isCustom = strategyId === "CUSTOM";

  const { data, isFetching, error } = useQuery({
    queryKey: ["quant-screen", strategyId, isCustom ? "custom" : strategyId],
    queryFn: ({ signal }) =>
      isCustom && customSpec
        ? screenQuantLabSpec(customSpec, signal)
        : fetchQuantLabScreen(strategyId, signal),
    enabled: open,
  });

  return (
    <Panel title="Multi-asset screen" testId="quant-screen">
      <p className="fso-quant-note">
        '{strategyName}' 전략을 저장된 모든 종목에 돌려 누적 수익으로 랭킹.
      </p>
      {!open ? (
        <button
          className="fso-chat-confirm"
          onClick={() => setOpen(true)}
          data-testid="quant-screen-run"
        >
          여러 종목에 돌려보기 ▶
        </button>
      ) : isFetching ? (
        <p className="fso-quant-note" role="status">
          전 종목 백테스트 중…
        </p>
      ) : error ? (
        <p className="fso-quant-empty" role="alert">
          스크리닝을 불러올 수 없습니다.
        </p>
      ) : data && data.rows.length > 0 ? (
        <table className="fso-quant-wf" data-testid="quant-screen-table">
          <thead>
            <tr>
              <th>종목</th>
              <th>누적</th>
              <th>Sharpe</th>
              <th>MDD</th>
              <th>보유</th>
              <th>매매</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr
                key={r.ticker}
                data-current={r.ticker === currentTicker}
                onClick={() => onPick(r.ticker)}
                className="fso-quant-screen-row"
              >
                <td>{r.ticker}</td>
                <td data-neg={(r.totalReturn ?? 0) < 0}>{pct(r.totalReturn)}</td>
                <td>{ratio(r.sharpe)}</td>
                <td>{pct(r.maxDrawdown)}</td>
                <td>{pct(r.exposurePct)}</td>
                <td>{r.roundTrips}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="fso-quant-empty">스크리닝할 종목이 없습니다.</p>
      )}
    </Panel>
  );
}
