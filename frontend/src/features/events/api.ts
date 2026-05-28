import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { eventRadarFixture } from "@/mocks/fixtures/eventRadar.fixture";
import type { EventRadarData } from "./types";

export async function fetchEventRadar(
  signal?: AbortSignal,
): Promise<EventRadarData> {
  try {
    return await getJson<EventRadarData>(apiEndpoints.eventRadar, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return eventRadarFixture;
  }
}
