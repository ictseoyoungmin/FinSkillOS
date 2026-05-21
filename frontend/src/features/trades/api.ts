import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { tradeMemoryFixture } from "@/mocks/fixtures/tradeMemory.fixture";
import type {
  TradeEntryInput,
  TradeEntryResult,
  TradeMemoryData,
  WeeklyReviewVM,
} from "./types";

export async function fetchTradeMemory(
  signal?: AbortSignal,
): Promise<TradeMemoryData> {
  try {
    return await getJson<TradeMemoryData>(apiEndpoints.tradeMemory, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return tradeMemoryFixture;
  }
}

export async function fetchWeeklyReview(
  signal?: AbortSignal,
): Promise<WeeklyReviewVM> {
  try {
    return await getJson<WeeklyReviewVM>(apiEndpoints.tradeWeeklyReview, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    return tradeMemoryFixture.weeklyReview;
  }
}

export async function submitTradeEntry(
  input: TradeEntryInput,
  signal?: AbortSignal,
): Promise<TradeEntryResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? "/api";
  const url = `${base}${apiEndpoints.tradeEntries}`;
  const response = await fetch(url, {
    method: "POST",
    credentials: "omit",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    signal,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `${response.status} ${response.statusText} for ${url}`,
    );
  }
  return (await response.json()) as TradeEntryResult;
}
