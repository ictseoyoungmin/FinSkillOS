import type { ReactNode } from "react";
import "./metric.css";

export interface MetricProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  testId?: string;
}

export function Metric({ label, value, hint, testId }: MetricProps) {
  return (
    <div className="fso-metric" data-testid={testId}>
      <div className="fso-metric-label">{label}</div>
      <div className="fso-metric-value">{value}</div>
      {hint ? <div className="fso-metric-hint">{hint}</div> : null}
    </div>
  );
}
