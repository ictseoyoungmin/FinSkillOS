import type { ReactNode } from "react";
import "./card.css";

export interface CardProps {
  children: ReactNode;
  className?: string;
  testId?: string;
}

/**
 * Lower-weight container than `<Panel>` — no title bar, used for inner
 * groupings (e.g. interpretation cards, item rows).
 */
export function Card({ children, className, testId }: CardProps) {
  return (
    <div
      className={`fso-card ${className ?? ""}`.trim()}
      data-testid={testId}
    >
      {children}
    </div>
  );
}
