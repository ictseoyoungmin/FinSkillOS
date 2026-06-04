export const apiEndpoints = {
  health: "/health",
  systemStatus: "/system-status",
  controlRoom: "/control-room",
  controlRoomMock: "/mock/control-room",
  marketKernel: "/market-kernel",
  analysisWorkspace: "/analysis-workspace",
  symbolLab: "/symbol-lab",
  symbolSubscriptionFolders: "/symbol-lab/subscription-folders",
  riskFirewall: "/risk-firewall",
  missionControl: "/mission-control",
  systemOps: "/system-ops",
  collectionControl: "/system-ops/collection-control",
  newsIntelligence: "/news-intelligence",
  eventRadar: "/event-radar",
  tradeMemory: "/trade-memory",
  tradeEntries: "/trade-memory/entries",
  tradeWeeklyReview: "/trade-memory/weekly-review",
  tradeWeeklyEvidenceReport: "/trade-memory/weekly-evidence-report",
  tradeExport: "/trade-memory/export.csv",
  tradeImport: "/trade-memory/import",
} as const;

export type ApiEndpoint = (typeof apiEndpoints)[keyof typeof apiEndpoints];
