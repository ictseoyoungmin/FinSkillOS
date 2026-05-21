import type { RiskFirewallData } from "@/features/risk-guards/types";

/**
 * Mirrors api/fixtures/risk_firewall.py. Used when the API is offline
 * so the Risk Firewall page still renders. Kept in sync by hand;
 * backend tests assert the camelCase shape stays consistent.
 */
export const riskFirewallFixture: RiskFirewallData = {
  generatedAt: "2026-05-20T12:00:00+09:00",
  source: "fixture",
  systemStatus: { db: "LIVE", mode: "READ_MODE", guardCount: 3 },
  overallStatus: "FAIL",
  overallRiskLevel: "RED",
  guards: [
    {
      name: "SINGLE_POSITION_LIMIT_GUARD",
      status: "WARN",
      riskLevel: "YELLOW",
      title: "Single Position Limit",
      message: "TSLA exceeds configured ₩10M review threshold.",
    },
    {
      name: "DRAWDOWN_GUARD",
      status: "PASS",
      riskLevel: "GREEN",
      title: "Drawdown Guard",
      message: "Current drawdown is below the defensive threshold.",
    },
    {
      name: "SECTOR_CONCENTRATION_GUARD",
      status: "FAIL",
      riskLevel: "RED",
      title: "Sector Concentration",
      message: "AI / Semis exposure requires monitoring before adding risk.",
    },
    {
      name: "CASH_RATIO_GUARD",
      status: "PASS",
      riskLevel: "GREEN",
      title: "Cash Ratio",
      message: "Cash buffer is within the descriptive defensive band.",
    },
    {
      name: "REGIME_RISK_GUARD",
      status: "WARN",
      riskLevel: "YELLOW",
      title: "Regime Risk",
      message: "Regime is Risk-On but extended; volatility note active.",
    },
    {
      name: "OVERHEAT_ENTRY_GUARD",
      status: "WARN",
      riskLevel: "YELLOW",
      title: "Overheat Entry",
      message: "RSI elevation across AI / Semis leadership.",
    },
    {
      name: "GOAL_PROTECTION_GUARD",
      status: "INFO",
      riskLevel: "GREEN",
      title: "Goal Protection",
      message: "Goal progress at 73.4% · COMPLETION_GUARD watch.",
    },
    {
      name: "EVENT_PLACEHOLDER_GUARD",
      status: "INFO",
      riskLevel: "UNKNOWN",
      title: "Event Placeholder",
      message: "Event-driven volatility note tracked via Catalyst Watch.",
    },
  ],
  activeAlerts: [
    {
      alertDate: "2026-05-19",
      severity: "YELLOW",
      guardName: "SINGLE_POSITION_LIMIT_GUARD",
      title: "Single Position Limit",
      message: "TSLA exceeds configured ₩10M review threshold.",
    },
    {
      alertDate: "2026-05-19",
      severity: "RED",
      guardName: "SECTOR_CONCENTRATION_GUARD",
      title: "Sector Concentration",
      message: "AI / Semis exposure requires monitoring before adding risk.",
    },
    {
      alertDate: "2026-05-19",
      severity: "YELLOW",
      guardName: "REGIME_RISK_GUARD",
      title: "Regime Risk",
      message: "Risk-On but extended · monitor volatility cluster.",
    },
  ],
  protocol: [
    {
      tone: "allowed",
      label: "Allowed",
      description:
        "Review, journal, monitor, refresh stored views. The page never modifies positions.",
    },
    {
      tone: "limited",
      label: "Limited",
      description:
        "Exposure-size review remains required while concentration or overheat flags remain active.",
    },
    {
      tone: "blocked",
      label: "Block Add",
      description:
        "Execution commands and guaranteed-return language are blocked by contract. Risk Firewall is descriptive only.",
    },
  ],
  safetyCaption: "Read mode — this view never modifies positions.",
};
