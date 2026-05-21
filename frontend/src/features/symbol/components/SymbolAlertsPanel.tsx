import { Badge, EmptyState, Panel } from "@/shared/ui";
import type { SymbolAlert } from "../types";
import "./symbol-alerts-panel.css";

export interface SymbolAlertsPanelProps {
  alerts: SymbolAlert[];
}

const SEVERITY_TONE: Record<string, "info" | "warning" | "danger"> = {
  INFO: "info",
  WARN: "warning",
  CRITICAL: "danger",
  FAIL: "danger",
};

export function SymbolAlertsPanel({ alerts }: SymbolAlertsPanelProps) {
  return (
    <Panel
      title="Symbol Alerts"
      badge={`${alerts.length}`}
      badgeTone={alerts.length > 0 ? "warning" : "neutral"}
      testId="symbol-alerts-panel"
    >
      {alerts.length === 0 ? (
        <EmptyState
          title="No active alerts"
          message="No risk-guard alerts mention this ticker in the stored data."
        />
      ) : (
        <ul className="fso-symbol-alerts">
          {alerts.map((alert) => (
            <li key={`${alert.guardName}-${alert.alertDate}`}>
              <div className="fso-symbol-alert-head">
                <strong>{alert.title}</strong>
                <Badge tone={SEVERITY_TONE[alert.severity] ?? "neutral"}>
                  {alert.severity}
                </Badge>
              </div>
              <p className="fso-symbol-alert-msg">{alert.message}</p>
              <small className="fso-symbol-alert-meta">
                {alert.guardName} · {alert.alertDate}
              </small>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
