import type {
  EvidenceConflictData,
  EvidenceDriverData,
  EvidenceWatchpointData,
  IntegratedInterpretationData,
  JudgmentHeaderData,
} from "@/shared/types/evidence";

export type GuardStatus = "PASS" | "WARN" | "FAIL" | "BLOCKED" | "INFO";
export type RiskLevel = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "UNKNOWN";
export type AlertSeverity = "INFO" | "YELLOW" | "ORANGE" | "RED";
export type RiskProtocolTone = "allowed" | "limited" | "blocked";

export interface GuardDriver {
  label: string;
  value: string;
}

export interface GuardSummary {
  name: string;
  status: GuardStatus;
  riskLevel: RiskLevel;
  title: string;
  message: string;
  // Slice 163: per-guard evidence + review actions (live Risk Firewall only;
  // optional so Control Room / fixtures stay unchanged).
  attribution?: GuardDriver[];
  watchNext?: string[];
}

export interface ActiveAlertItem {
  alertDate: string;
  severity: AlertSeverity;
  guardName: string;
  title: string;
  message: string;
}

export interface RiskProtocolEntry {
  tone: RiskProtocolTone;
  label: string;
  description: string;
}

export interface RiskFirewallSystemStatus {
  db: string;
  mode: string;
  guardCount: number;
}

export interface AppliedSkillRule {
  skillId: string;
  version: string;
  firedRuleIds: string[];
  status: GuardStatus;
  riskLevel: RiskLevel;
}

export interface RiskFirewallDataState {
  evaluationSource: "fixture" | "live";
  evaluationStatus: GuardStatus;
  highestRiskLevel: RiskLevel;
  guardCount: number;
  flaggedGuardCount: number;
  passCount: number;
  alertCount: number;
  persistedAlerts: boolean;
  sourceNote: string;
  reviewNote: string;
}

export interface RiskFirewallData {
  generatedAt: string;
  systemStatus: RiskFirewallSystemStatus;
  dataState: RiskFirewallDataState;
  judgment: JudgmentHeaderData;
  drivers: EvidenceDriverData[];
  conflicts: EvidenceConflictData[];
  interpretation: IntegratedInterpretationData;
  watchpoints: EvidenceWatchpointData[];
  overallStatus: GuardStatus;
  overallRiskLevel: RiskLevel;
  guards: GuardSummary[];
  activeAlerts: ActiveAlertItem[];
  protocol: RiskProtocolEntry[];
  appliedRules: AppliedSkillRule[];
  safetyCaption: string;
  source: "fixture" | "live";
}
