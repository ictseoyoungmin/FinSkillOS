export const apiEndpoints = {
  health: "/health",
  controlRoom: "/control-room",
  controlRoomMock: "/mock/control-room",
  marketKernel: "/market-kernel",
  analysisWorkspace: "/analysis-workspace",
  symbolLab: "/symbol-lab",
  riskFirewall: "/risk-firewall",
  missionControl: "/mission-control",
  systemOps: "/system-ops",
} as const;

export type ApiEndpoint = (typeof apiEndpoints)[keyof typeof apiEndpoints];
