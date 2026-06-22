import { Panel } from "@/shared/ui";
import type { QuantWindow } from "../types";

export interface QuantWalkForwardPanelProps {
  windows: QuantWindow[];
}

function pct(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : `${(v * 100).toFixed(1)}%`;
}

function ratio(v: number | null): string {
  return v === null || !Number.isFinite(v) ? "—" : v.toFixed(2);
}

/**
 * Walk-forward robustness: the same strategy run over sequential time windows
 * (each restarts fresh). Consistent returns across windows = robust; one great
 * window carrying the rest = fragile. Descriptive observation, not advice.
 */
export function QuantWalkForwardPanel({ windows }: QuantWalkForwardPanelProps) {
  if (windows.length === 0) return null;
  return (
    <Panel title="Walk-forward robustness" testId="quant-walk-forward">
      <p className="fso-quant-note">
        전략을 {windows.length}개 기간으로 나눠 각각 독립 실행 — 기간마다 결과가 고르면
        견고, 한 기간이 전체를 끌어올리면 취약.
      </p>
      <table className="fso-quant-wf" data-testid="quant-wf-table">
        <thead>
          <tr>
            <th>기간</th>
            <th>구간</th>
            <th>누적</th>
            <th>Sharpe</th>
            <th>보유</th>
            <th>매수/매도</th>
          </tr>
        </thead>
        <tbody>
          {windows.map((w) => (
            <tr key={w.index}>
              <td>#{w.index}</td>
              <td className="fso-quant-wf-span">
                {w.dateStart} → {w.dateEnd}
              </td>
              <td data-neg={(w.totalReturn ?? 0) < 0}>{pct(w.totalReturn)}</td>
              <td>{ratio(w.sharpe)}</td>
              <td>{pct(w.exposurePct)}</td>
              <td>{w.roundTrips}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}
