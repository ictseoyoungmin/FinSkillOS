import { Badge, Panel } from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { PortfolioConstraint } from "../types";
import "./constraint-summary-panel.css";

export interface ConstraintSummaryPanelProps {
  constraints: PortfolioConstraint[];
}

const STATUS_TONE: Record<PortfolioConstraint["status"], BadgeTone> = {
  OK: "success",
  WATCH: "warning",
  BREACH: "danger",
  UNKNOWN: "neutral",
};

const STATUS_LABEL: Record<PortfolioConstraint["status"], string> = {
  OK: "OK",
  WATCH: "Watch",
  BREACH: "Breach",
  UNKNOWN: "—",
};

/**
 * Consolidated portfolio constraint summary (Slice 166). Headroom against the
 * stored risk policy (single-position limit, cash reserve, drawdown).
 * Descriptive constraint state only — no execution controls.
 */
export function ConstraintSummaryPanel({
  constraints,
}: ConstraintSummaryPanelProps) {
  if (constraints.length === 0) {
    return null;
  }
  const worst = constraints.some((c) => c.status === "BREACH")
    ? "Breach"
    : constraints.some((c) => c.status === "WATCH")
      ? "Watch"
      : "OK";
  return (
    <Panel
      title="Constraint Summary"
      badge={worst}
      badgeTone={
        worst === "Breach" ? "danger" : worst === "Watch" ? "warning" : "success"
      }
      testId="constraint-summary"
    >
      <ul className="fso-constraint-list">
        {constraints.map((constraint) => (
          <li
            key={constraint.label}
            data-testid={`constraint-${constraint.label}`}
          >
            <div className="fso-constraint-head">
              <span className="fso-constraint-label">{constraint.label}</span>
              <Badge tone={STATUS_TONE[constraint.status]}>
                {STATUS_LABEL[constraint.status]}
              </Badge>
            </div>
            <p className="fso-constraint-detail">{constraint.detail}</p>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
