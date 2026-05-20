import type { CSSProperties, ReactNode } from "react";
import "./panel.css";

export interface PanelProps {
  title?: string;
  badge?: string;
  badgeTone?: "neutral" | "info" | "warning" | "danger" | "success";
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  /** Optional `data-testid` for e2e tests. */
  testId?: string;
}

/**
 * Bordered OS-style panel with optional title + badge. Mirrors the
 * v4.1 mockup's `.panel + .panel-head` markup so styling stays
 * consistent across pages and the Playwright visual baselines.
 */
export function Panel({
  title,
  badge,
  badgeTone = "neutral",
  children,
  className,
  style,
  testId,
}: PanelProps) {
  return (
    <section
      className={`fso-panel ${className ?? ""}`.trim()}
      style={style}
      data-testid={testId}
    >
      {(title ?? badge) ? (
        <header className="fso-panel-head">
          <span className="fso-panel-dots" aria-hidden>
            <span />
            <span />
            <span />
          </span>
          {title ? <h2 className="fso-panel-title">{title}</h2> : null}
          {badge ? (
            <span
              className={`fso-panel-badge fso-tone-${badgeTone}`}
              data-tone={badgeTone}
            >
              {badge}
            </span>
          ) : null}
        </header>
      ) : null}
      <div className="fso-panel-body">{children}</div>
    </section>
  );
}
