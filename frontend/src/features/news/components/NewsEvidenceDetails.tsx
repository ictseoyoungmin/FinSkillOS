import type { ReactNode } from "react";
import "./news-evidence-details.css";

export interface NewsEvidenceDetailsProps {
  badge: string;
  children: ReactNode;
  defaultOpen?: boolean;
  title: string;
}

export function NewsEvidenceDetails({
  badge,
  children,
  defaultOpen = false,
  title,
}: NewsEvidenceDetailsProps) {
  return (
    <details className="fso-news-evidence-details" open={defaultOpen}>
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
