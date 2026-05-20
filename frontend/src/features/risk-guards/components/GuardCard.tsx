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
    </Card>
  );
}
