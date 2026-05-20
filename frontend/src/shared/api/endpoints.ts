export const apiEndpoints = {
  health: "/health",
  controlRoom: "/control-room",
  controlRoomMock: "/mock/control-room",
} as const;

export type ApiEndpoint = (typeof apiEndpoints)[keyof typeof apiEndpoints];
