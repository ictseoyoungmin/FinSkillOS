import { Card } from "@/shared/ui";
import type { GuardSummary } from "../types";
import "./guard-card.css";

const STATUS_GLYPH: Record<GuardSummary["status"], string> = {
  PASS: "✓",
  WARN: "!",
  FAIL: "×",
  BLOCKED: "■",
  INFO: "•",
};

const STATUS_LABEL: Record<GuardSummary["status"], string> = {
  PASS: "Pass",
  WARN: "Limited",
  FAIL: "Block Add",
  BLOCKED: "Protected",
  INFO: "Info",
};

const STATUS_TONE: Record<GuardSummary["status"], string> = {
  PASS: "var(--fso-green)",
  WARN: "var(--fso-amber)",
  FAIL: "var(--fso-red)",
  BLOCKED: "var(--fso-red)",
  INFO: "var(--fso-cyan)",
};

export interface GuardCardProps {
  guard: GuardSummary;
}

export function GuardCard({ guard }: GuardCardProps) {
  const tone = STATUS_TONE[guard.status];
  const attribution = guard.attribution ?? [];
  const watchNext = guard.watchNext ?? [];
  const hasWhy = attribution.length > 0 || watchNext.length > 0;
  return (
    <Card testId={`guard-${guard.name}`}>
      <div className="fso-guard-row">
        <span
          className="fso-guard-icon"
          style={{ color: tone, borderColor: tone }}
          aria-hidden
        >
          {STATUS_GLYPH[guard.status]}
        </span>
        <div className="fso-guard-meta">
          <div className="fso-guard-title">{guard.title}</div>
          <p className="fso-guard-msg">{guard.message}</p>
        </div>
        <span className="fso-guard-tag" style={{ color: tone, borderColor: tone }}>
          {STATUS_LABEL[guard.status]}
        </span>
      </div>
      {hasWhy ? (
        <details
          className="fso-guard-why"
          data-testid={`guard-why-${guard.name}`}
        >
          <summary>Why this state?</summary>
          {attribution.length > 0 ? (
            <dl className="fso-guard-attribution">
              {attribution.map((row) => (
                <div key={row.label}>
                  <dt>{row.label}</dt>
                  <dd>{row.value}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          {watchNext.length > 0 ? (
            <ul className="fso-guard-watch-next">
              {watchNext.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
        </details>
      ) : null}
    </Card>
  );
}
