import { ApiError, getJson, sendJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import type {
  TradeEntryInput,
  TradeEntryResult,
  TradeImportResult,
  TradeMemoryData,
  WeeklyReviewVM,
} from "./types";

export async function fetchTradeMemory(
  signal?: AbortSignal,
): Promise<TradeMemoryData> {
  return await getJson<TradeMemoryData>(apiEndpoints.tradeMemory, { signal });
}

export async function fetchWeeklyReview(
  signal?: AbortSignal,
): Promise<WeeklyReviewVM> {
  return await getJson<WeeklyReviewVM>(apiEndpoints.tradeWeeklyReview, {
    signal,
  });
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

// --- Slice 160: CSV import (dry-run preview → confirm, append-only) ---------

/** Dry-run an import (per-row OK/INVALID preview); never writes. */
export async function previewTradeImport(
  csvText: string,
): Promise<TradeImportResult> {
  return await sendJson<TradeImportResult>(
    apiEndpoints.tradeImport,
    "POST",
    { csvText },
  );
}

/** Apply an import (append). Rejects the whole batch if any row is invalid. */
export async function applyTradeImport(
  csvText: string,
): Promise<TradeImportResult> {
  return await sendJson<TradeImportResult>(
    `${apiEndpoints.tradeImport}?confirm=true`,
    "POST",
    { csvText },
  );
}
