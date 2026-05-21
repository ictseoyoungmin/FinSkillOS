import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { missionControlFixture } from "@/mocks/fixtures/missionControl.fixture";
import type { MissionControlData } from "./types";

/**
 * Read the Mission Control snapshot. Follows the same fixture
 * fallback pattern Slice 13.6 / 13.7 use — network / 4xx errors
 * degrade to the deterministic fixture so the cockpit stays
 * renderable; 5xx errors still surface so users notice real API
 * outages.
 */
export async function fetchMissionControl(
  signal?: AbortSignal,
): Promise<MissionControlData> {
  try {
    return await getJson<MissionControlData>(apiEndpoints.missionControl, {
      signal,
    });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return missionControlFixture;
  }
}
