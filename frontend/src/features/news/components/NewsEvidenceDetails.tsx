import type { ReactNode } from "react";
import "./news-evidence-details.css";

export interface NewsEvidenceDetailsProps {
  badge: string;
  children: ReactNode;
  defaultOpen?: boolean;
  testId?: string;
  title: string;
}

export function NewsEvidenceDetails({
  badge,
  children,
  defaultOpen = false,
  testId,
  title,
}: NewsEvidenceDetailsProps) {
  return (
    <details
      className="fso-news-evidence-details"
      data-testid={testId}
      open={defaultOpen}
    >
      <summary>
        <span className="fso-news-evidence-dots" aria-hidden>
          <span />
          <span />
          <span />
        </span>
        <strong>{title}</strong>
        <span className="fso-news-evidence-badge">{badge}</span>
      </summary>
      <div className="fso-news-evidence-body">{children}</div>
    </details>
  );
}
