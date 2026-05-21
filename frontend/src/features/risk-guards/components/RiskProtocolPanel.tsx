import { Panel } from "@/shared/ui";
import type { RiskProtocolEntry, RiskProtocolTone } from "../types";
import "./risk-protocol-panel.css";

export interface RiskProtocolPanelProps {
  protocol: RiskProtocolEntry[];
  safetyCaption: string;
}

const TONE_COLOR: Record<RiskProtocolTone, string> = {
  allowed: "var(--fso-green)",
  limited: "var(--fso-amber)",
  blocked: "var(--fso-red)",
};

/**
 * Risk Firewall "Allowed / Limited / Block Add" panel. Shows the
 * read-only safety contract that the Streamlit page also documents:
 * the firewall is descriptive only, never an execution surface.
 */
export function RiskProtocolPanel({
  protocol,
  safetyCaption,
}: RiskProtocolPanelProps) {
  return (
    <Panel
      title="Risk Protocol"
      badge="Read mode"
      badgeTone="info"
      testId="risk-firewall-protocol"
    >
      <ul className="fso-risk-protocol-list">
        {protocol.map((entry) => {
          const tone = TONE_COLOR[entry.tone];
          return (
            <li className="fso-risk-protocol-row" key={entry.tone}>
              <span
                className="fso-risk-protocol-tag"
                style={{ color: tone, borderColor: tone }}
                data-tone={entry.tone}
              >
                {entry.label}
              </span>
              <p className="fso-risk-protocol-desc">{entry.description}</p>
            </li>
          );
        })}
      </ul>
      <p
        className="fso-risk-protocol-safety"
        data-testid="risk-firewall-safety-caption"
      >
        {safetyCaption}
      </p>
    </Panel>
  );
}
