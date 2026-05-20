import type { ReactNode } from "react";
import "./badge.css";

export type BadgeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "purple";

export interface BadgeProps {
  tone?: BadgeTone;
  children: ReactNode;
  className?: string;
  testId?: string;
}

export function Badge({
  tone = "neutral",
  children,
  className,
  testId,
}: BadgeProps) {
  return (
    <span
      className={`fso-badge fso-tone-${tone} ${className ?? ""}`.trim()}
      data-tone={tone}
      data-testid={testId}
    >
      {children}
    </span>
  );
}
