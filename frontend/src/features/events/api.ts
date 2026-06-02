import { getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type { EventRadarData } from "./types";

export async function fetchEventRadar(
  signal?: AbortSignal,
): Promise<EventRadarData> {
  return await getJson<EventRadarData>(apiEndpoints.eventRadar, { signal });
}
