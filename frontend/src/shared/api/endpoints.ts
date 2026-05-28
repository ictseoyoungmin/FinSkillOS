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
  newsIntelligence: "/news-intelligence",
  eventRadar: "/event-radar",
  eventManualEvent: "/event-radar/manual-event",
  eventSeedSampleEvents: "/event-radar/seed-sample-events",
  tradeMemory: "/trade-memory",
  tradeEntries: "/trade-memory/entries",
  tradeWeeklyReview: "/trade-memory/weekly-review",
} as const;

export type ApiEndpoint = (typeof apiEndpoints)[keyof typeof apiEndpoints];
