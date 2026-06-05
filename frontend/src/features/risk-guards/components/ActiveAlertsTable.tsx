import { Pagination, Panel } from "@/shared/ui";
import { usePagination } from "@/shared/hooks/usePagination";
import type { ActiveAlertItem, AlertSeverity } from "../types";
import "./active-alerts-table.css";

const PAGE_SIZE = 8;

export interface ActiveAlertsTableProps {
  alerts: ActiveAlertItem[];
}

const SEVERITY_TONE: Record<AlertSeverity, string> = {
  INFO: "var(--fso-cyan)",
  YELLOW: "var(--fso-amber)",
  ORANGE: "var(--fso-amber)",
  RED: "var(--fso-red)",
};

const SEVERITY_LABEL: Record<AlertSeverity, string> = {
  INFO: "Info",
  YELLOW: "Yellow",
  ORANGE: "Orange",
  RED: "Red",
};

/**
 * Risk Firewall "Active Alerts" table — read-only listing of the
 * Slice-06 same-day unresolved alerts. Date / severity / guard /
 * title / message columns mirror what `RiskGuardService.get_active_alerts`
 * exposes via the API. No row-level actions exist — the page never
 * modifies positions.
 */
export function ActiveAlertsTable({ alerts }: ActiveAlertsTableProps) {
  const { visible, page, pageCount, prev, next } = usePagination(
    alerts,
    PAGE_SIZE,
  );
  if (alerts.length === 0) {
    return (
      <Panel
        title="Active Alerts"
        badge="0"
        badgeTone="success"
        testId="active-alerts"
      >
        <p className="fso-active-alerts-empty">
          No active alerts at the snapshot time.
        </p>
      </Panel>
    );
  }
  return (
    <Panel
      title="Active Alerts"
      badge={String(alerts.length)}
      badgeTone="warning"
      testId="active-alerts"
    >
      <table
        className="fso-active-alerts-table"
        data-testid="risk-firewall-active-alerts-table"
      >
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Severity</th>
            <th scope="col">Guard</th>
            <th scope="col">Title</th>
            <th scope="col">Message</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((alert, index) => {
            const tone = SEVERITY_TONE[alert.severity];
            const key = `${alert.guardName}-${alert.alertDate}-${index}`;
            return (
              <tr key={key}>
                <td className="fso-active-alerts-date">{alert.alertDate}</td>
                <td>
                  <span
                    className="fso-active-alerts-pill"
                    style={{ color: tone, borderColor: tone }}
                  >
                    {SEVERITY_LABEL[alert.severity]}
                  </span>
                </td>
                <td className="fso-active-alerts-guard">{alert.guardName}</td>
                <td>{alert.title}</td>
                <td className="fso-active-alerts-message">{alert.message}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <Pagination
        page={page}
        pageCount={pageCount}
        onPrev={prev}
        onNext={next}
        label="Active alerts pagination"
      />
    </Panel>
  );
}
