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

function apiBase(): string {
  return import.meta.env.VITE_API_BASE_URL ?? "/api";
}

async function sendTradeEntry(
  method: "POST" | "PUT" | "DELETE",
  url: string,
  input?: TradeEntryInput,
  signal?: AbortSignal,
): Promise<TradeEntryResult> {
  const response = await fetch(url, {
    method,
    credentials: "omit",
    headers: {
      Accept: "application/json",
      ...(input ? { "Content-Type": "application/json" } : {}),
    },
    body: input ? JSON.stringify(input) : undefined,
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

export async function submitTradeEntry(
  input: TradeEntryInput,
  signal?: AbortSignal,
): Promise<TradeEntryResult> {
  return sendTradeEntry(
    "POST",
    `${apiBase()}${apiEndpoints.tradeEntries}`,
    input,
    signal,
  );
}

export async function updateTradeEntry(
  entryId: string,
  input: TradeEntryInput,
  signal?: AbortSignal,
): Promise<TradeEntryResult> {
  return sendTradeEntry(
    "PUT",
    `${apiBase()}${apiEndpoints.tradeEntries}/${entryId}`,
    input,
    signal,
  );
}

export async function deleteTradeEntry(
  entryId: string,
  signal?: AbortSignal,
): Promise<TradeEntryResult> {
  return sendTradeEntry(
    "DELETE",
    `${apiBase()}${apiEndpoints.tradeEntries}/${entryId}`,
    undefined,
    signal,
  );
}

export function tradeMemoryCsvUrl(): string {
  return `${apiBase()}${apiEndpoints.tradeExport}`;
}
