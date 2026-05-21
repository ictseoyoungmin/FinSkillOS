export type GuardStatus = "PASS" | "WARN" | "FAIL" | "BLOCKED" | "INFO";
export type RiskLevel = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "UNKNOWN";
export type AlertSeverity = "INFO" | "YELLOW" | "ORANGE" | "RED";
export type RiskProtocolTone = "allowed" | "limited" | "blocked";

export interface GuardSummary {
  name: string;
  status: GuardStatus;
  riskLevel: RiskLevel;
  title: string;
  message: string;
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

export interface RiskFirewallData {
  generatedAt: string;
  systemStatus: RiskFirewallSystemStatus;
  overallStatus: GuardStatus;
  overallRiskLevel: RiskLevel;
  guards: GuardSummary[];
  activeAlerts: ActiveAlertItem[];
  protocol: RiskProtocolEntry[];
  safetyCaption: string;
  source: "fixture" | "live";
}
