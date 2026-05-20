export type GuardStatus = "PASS" | "WARN" | "FAIL" | "BLOCKED" | "INFO";
export type RiskLevel = "GREEN" | "YELLOW" | "ORANGE" | "RED" | "UNKNOWN";

export interface GuardSummary {
  name: string;
  status: GuardStatus;
  riskLevel: RiskLevel;
  title: string;
  message: string;
}
