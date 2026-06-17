import { Badge, Panel } from "@/shared/ui";
import type { BadgeTone } from "@/shared/ui/Badge";
import type { AppliedSkillRule, GuardStatus } from "../types";
import "./applied-skill-rules-panel.css";

export interface AppliedSkillRulesPanelProps {
  rules: AppliedSkillRule[];
}

const STATUS_TONE: Record<GuardStatus, BadgeTone> = {
  PASS: "success",
  INFO: "neutral",
  WARN: "warning",
  FAIL: "danger",
  BLOCKED: "danger",
};

/**
 * "Applied Skill Rules" audit trail (Phase 20.2c) — which skill rule fired per
 * risk skill in the live evaluation. Revives the v1 Skills.md audit: every
 * verdict is traceable to a stable Rule ID, not an opaque guard.
 */
export function AppliedSkillRulesPanel({ rules }: AppliedSkillRulesPanelProps) {
  if (rules.length === 0) {
    return null;
  }
  return (
    <Panel
      title="Applied Skill Rules"
      badge={`${rules.length}`}
      badgeTone="info"
      testId="applied-skill-rules"
    >
      <ul className="fso-applied-rules-list">
        {rules.map((rule) => (
          <li className="fso-applied-rules-row" key={rule.skillId}>
            <span className="fso-applied-rules-skill">
              {rule.skillId.replace(/^RISK\./, "")}
            </span>
            <code className="fso-applied-rules-id">
              {rule.firedRuleIds.join(" · ")}
            </code>
            <Badge tone={STATUS_TONE[rule.status]}>{rule.status}</Badge>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
