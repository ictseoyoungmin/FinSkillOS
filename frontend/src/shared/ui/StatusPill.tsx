import type { ReactNode } from "react";
import { Badge, type BadgeTone } from "./Badge";

export interface StatusPillProps {
  label: string;
  tone?: BadgeTone;
  children?: ReactNode;
  testId?: string;
}

/**
 * Convenience around `<Badge>` for the OS tray pills. Adds an
 * optional `data-testid` so the e2e tests can target a specific pill
 * (e.g. `db-status-pill`) without picking up neighbouring badges.
 */
export function StatusPill({
  label,
  tone = "neutral",
  children,
  testId,
}: StatusPillProps) {
  return (
    <Badge tone={tone} testId={testId}>
      {label}
      {children ? <span style={{ marginLeft: 4 }}>{children}</span> : null}
    </Badge>
  );
}
