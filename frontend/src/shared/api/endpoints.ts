export const apiEndpoints = {
  health: "/health",
  controlRoom: "/control-room",
  controlRoomMock: "/mock/control-room",
  marketKernel: "/market-kernel",
  analysisWorkspace: "/analysis-workspace",
  symbolLab: "/symbol-lab",
} as const;

export type ApiEndpoint = (typeof apiEndpoints)[keyof typeof apiEndpoints];
