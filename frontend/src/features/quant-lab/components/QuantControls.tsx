import { Panel } from "@/shared/ui";
import type { QuantStrategyOption } from "../types";

export interface QuantControlsProps {
  strategies: QuantStrategyOption[];
  tickers: string[];
  selectedStrategy: string;
  selectedTicker: string;
  busy: boolean;
  onStrategyChange: (id: string) => void;
  onTickerChange: (ticker: string) => void;
}

/**
 * Strategy + ticker selectors. Picking a built-in spec re-runs the simulation;
 * the agent authors new specs in Phase 21.4.
 */
export function QuantControls({
  strategies,
  tickers,
  selectedStrategy,
  selectedTicker,
  busy,
  onStrategyChange,
  onTickerChange,
}: QuantControlsProps) {
  const active = strategies.find((s) => s.id === selectedStrategy);
  return (
    <Panel title="Simulation setup" testId="quant-controls">
      <div className="fso-quant-controls">
        <label className="fso-quant-field">
          <span>전략 (가설)</span>
          <select
            value={selectedStrategy}
            disabled={busy}
            onChange={(e) => onStrategyChange(e.target.value)}
            data-testid="quant-strategy-select"
          >
            {strategies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="fso-quant-field">
          <span>대상 종목</span>
          <select
            value={selectedTicker}
            disabled={busy}
            onChange={(e) => onTickerChange(e.target.value)}
            data-testid="quant-ticker-select"
          >
            {tickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </div>
      {active ? <p className="fso-quant-note">{active.description}</p> : null}
    </Panel>
  );
}
