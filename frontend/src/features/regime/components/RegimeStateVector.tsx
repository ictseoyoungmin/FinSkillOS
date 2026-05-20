import { Panel } from "@/shared/ui";
import type { OperatingState } from "../types";
import "./regime-state-vector.css";

const VECTOR_DEFS = [
  { key: "trend", label: "Trend Stack" },
  { key: "rsi", label: "RSI Zone" },
  { key: "vix", label: "Vol Proxy" },
  { key: "macro", label: "Macro Pressure" },
  { key: "events", label: "Event Cluster" },
] as const;

function derive(state: OperatingState, key: (typeof VECTOR_DEFS)[number]["key"]) {
  const score = state.preparationScore;
  switch (key) {
    case "trend":
      return { value: "Bullish", tone: score > 60 ? "var(--fso-green)" : "var(--fso-amber)" };
    case "rsi":
      return { value: "Elevated", tone: "var(--fso-amber)" };
    case "vix":
      return { value: "Compressed", tone: "var(--fso-amber)" };
    case "macro":
      return { value: "Neutral", tone: "var(--fso-text-muted)" };
    case "events":
      return { value: "Cluster", tone: "var(--fso-red)" };
    default:
      return { value: "—", tone: "var(--fso-text-muted)" };
  }
}

export interface RegimeStateVectorProps {
  state: OperatingState;
}

export function RegimeStateVector({ state }: RegimeStateVectorProps) {
  return (
    <Panel
      title="State Vector"
      badge="Deterministic"
      testId="regime-state-vector"
    >
      <ul className="fso-vector-grid">
        {VECTOR_DEFS.map((def) => {
          const { value, tone } = derive(state, def.key);
          return (
            <li className="fso-vector-cell" key={def.key}>
              <span className="fso-vector-label">{def.label}</span>
              <span className="fso-vector-value" style={{ color: tone }}>
                {value}
              </span>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
