import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { ControlRoomData } from "./types";

/**
 * Read the Control Room snapshot.
 *
 * Slice 119: live read errors surface to React Query instead of degrading
 * silently to the fixture. The page keeps a deterministic placeholder shape,
 * but marks it as sample shape when the live request fails.
 */
export async function fetchControlRoom(
  signal?: AbortSignal,
): Promise<ControlRoomData> {
  return await getJson<ControlRoomData>(apiEndpoints.controlRoom, { signal });
}
