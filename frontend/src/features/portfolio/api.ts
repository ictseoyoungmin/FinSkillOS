import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { MissionControlData } from "./types";

/**
 * Read the Mission Control snapshot.
 *
 * Slice 119: errors surface to React Query. The page may keep the deterministic
 * placeholder shape, but failed live evidence must be visible.
 */
export async function fetchMissionControl(
  signal?: AbortSignal,
): Promise<MissionControlData> {
  return await getJson<MissionControlData>(apiEndpoints.missionControl, {
    signal,
  });
}
