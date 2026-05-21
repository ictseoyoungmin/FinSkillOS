import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { eventRadarFixture } from "@/mocks/fixtures/eventRadar.fixture";
import type {
  EventRadarData,
  ManualEventInput,
  ManualEventResult,
  SeedEventsResult,
} from "./types";

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

async function postJson<TResp>(
  path: string,
  body: unknown,
  signal?: AbortSignal,
): Promise<TResp> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}${path}`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as TResp;
}

export function submitManualEvent(
  input: ManualEventInput,
  signal?: AbortSignal,
): Promise<ManualEventResult> {
  return postJson<ManualEventResult>(apiEndpoints.eventManualEvent, input, signal);
}

export function runEventSeedSampleEvents(
  signal?: AbortSignal,
): Promise<SeedEventsResult> {
  return postJson<SeedEventsResult>(apiEndpoints.eventSeedSampleEvents, undefined, signal);
}
