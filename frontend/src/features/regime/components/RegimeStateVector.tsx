import { Panel } from "@/shared/ui";
import type { OperatingState, StateVectorTone } from "../types";
import "./regime-state-vector.css";

const TONE_COLOR: Record<StateVectorTone, string> = {
  success: "var(--fso-green)",
  warning: "var(--fso-amber)",
  danger: "var(--fso-red)",
  info: "var(--fso-cyan)",
  neutral: "var(--fso-text-muted)",
};

export interface RegimeStateVectorProps {
  state: OperatingState;
}

/**
 * Compact operating-state vector. Every cell is real regime evidence published
 * by the API (decision mode, classification confidence, and the rule-derived
 * positive / risk factors) — no fabricated trend / RSI / vol readings. When no
 * regime has been classified the panel says so honestly.
 */
export function RegimeStateVector({ state }: RegimeStateVectorProps) {
  const cells = state.stateVector ?? [];
  return (
    <Panel
      title="State Vector"
      badge="Regime evidence"
      testId="regime-state-vector"
    >
      {cells.length === 0 ? (
        <p className="fso-vector-empty">
          No regime classification is available yet, so there is no state
          evidence to vector.
        </p>
      ) : (
        <ul className="fso-vector-grid">
          {cells.map((cell, index) => (
            <li className="fso-vector-cell" key={`${cell.label}-${index}`}>
              <span className="fso-vector-label">{cell.label}</span>
              <span
                className="fso-vector-value"
                style={{ color: TONE_COLOR[cell.tone] }}
              >
                {cell.value}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
